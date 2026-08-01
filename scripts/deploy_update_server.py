# -*- coding: utf-8 -*-
"""部署御衡热更新服务器到腾讯云(49.234.196.103, WinServer2012R2, WinRM)
用法: python deploy_update_server.py [version]
流程: 建目录 -> 传 serve_update.py -> 传 version.json + www-<version>.zip -> 启动 -> 公网验证
"""
import base64
import json
import os
import subprocess
import sys

IP = "49.234.196.103"
USER = "Administrator"
PWD = "77585213aA@."  # 腾讯云 WinServer2012R2 管理员密码
REMOTE_DIR = r"C:\hermes-update"

LOCAL_SCRIPTS = os.path.dirname(os.path.abspath(__file__))


def get_session():
    try:
        import winrm
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "pywinrm", "-q"], check=True)
        import winrm
    return winrm.Session(f"http://{IP}:5985/wsman", auth=(USER, PWD), transport="basic")


def run(s, cmd):
    r = s.run_cmd("cmd", ["/c", cmd])
    return r.std_out.decode("utf-8", errors="ignore"), r.std_err.decode("utf-8", errors="ignore"), r.status_code


def push_file(s, local_path, remote_path):
    """base64分块+echo+certutil解码 (WinRM无SFTP)"""
    data = base64.b64encode(open(local_path, "rb").read()).decode()
    b64_tmp = remote_path + ".b64"
    run(s, f"del /f {b64_tmp} >nul 2>&1")
    chunk = 3800
    for i in range(0, len(data), chunk):
        piece = data[i:i + chunk]
        r = s.run_cmd("cmd", ["/c", f"echo {piece}>>{b64_tmp}"])
        if r.status_code != 0:
            print("  echo chunk FAIL", r.status_code)
            return False
    r = s.run_cmd("cmd", ["/c", f"certutil -decode -f {b64_tmp} {remote_path} >nul"])
    if r.status_code != 0:
        print("  certutil decode FAIL", r.status_code)
        return False
    # 校验大小
    out, _, _ = run(s, f"for %A in ({remote_path}) do @echo %~zA")
    remote_size = out.strip().split("\n")[-1].strip()
    local_size = os.path.getsize(local_path)
    ok = str(local_size) == str(remote_size)
    print(f"  {'✅' if ok else '❌'} {os.path.basename(local_path)}: {local_size} vs {remote_size}")
    run(s, f"del /f {b64_tmp} >nul 2>&1")
    return ok


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "1.6"
    pub_dir = os.path.normpath(os.path.join(LOCAL_SCRIPTS, "..", "..", "hermes-update-publish"))
    if not os.path.isdir(pub_dir):
        # 回退: /tmp/hermes-update-test
        pub_dir = "/tmp/hermes-update-test" if os.path.isdir("/tmp/hermes-update-test") else None
    if not pub_dir or not os.path.exists(os.path.join(pub_dir, "version.json")):
        print(f"❌ 找不到打包产物目录: {pub_dir} — 先跑 make-update-package.py")
        sys.exit(1)

    print(f"连接 {IP} ...")
    s = get_session()
    out, err, _ = run(s, "whoami")
    print("whoami:", out.strip() or err.strip())

    print(f"建目录 {REMOTE_DIR}")
    run(s, f"if not exist {REMOTE_DIR} mkdir {REMOTE_DIR}")

    print("传 serve_update.py")
    if not push_file(s, os.path.join(LOCAL_SCRIPTS, "serve_update.py"), REMOTE_DIR + r"\serve_update.py"):
        sys.exit(1)
    print("传 version.json")
    if not push_file(s, os.path.join(pub_dir, "version.json"), REMOTE_DIR + r"\version.json"):
        sys.exit(1)
    zip_name = f"www-{version}.zip"
    print(f"传 {zip_name}")
    if not push_file(s, os.path.join(pub_dir, zip_name), REMOTE_DIR + "\\" + zip_name):
        sys.exit(1)

    # 检查/启动服务器 (若端口已被占用则跳过启动)
    out, _, _ = run(s, "netstat -ano | findstr :8401 | findstr LISTENING")
    if "8401" in out:
        print("8401 已在监听, 跳过启动")
    else:
        print("启动 serve_update.py (后台, WinRM会挂住属正常)")
        # 找python路径
        out, _, _ = run(s, 'where python')
        py = out.strip().split("\n")[0] if out.strip() else r"C:\Python311\python.exe"
        print("python:", py)
        s.run_cmd("cmd", ["/c", f'start /b "" "{py}" "{REMOTE_DIR}\\serve_update.py" 8401 > {REMOTE_DIR}\\serve.log 2>&1'])
        import time
        time.sleep(6)

    out, _, _ = run(s, "netstat -ano | findstr :8401 | findstr LISTENING")
    print("监听检查:", "✅" if "8401" in out else f"❌ {out}")

    # 公网验证
    import urllib.request
    for url in [f"http://{IP}:8401/version.json", f"http://{IP}:8401/{zip_name}"]:
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                body = resp.read(300)
                print(f"✅ 公网可达 {url} -> {resp.status} {len(body)}B")
        except Exception as e:
            print(f"❌ 公网不可达 {url}: {e}")


if __name__ == "__main__":
    main()
