#!/usr/bin/env python3
"""
御衡 Web资源热更新打包脚本
用法: python make-update-package.py <version> [www_dir] [out_dir]
示例: python make-update-package.py 1.6 www ../hermes-update-publish

产出:
  out_dir/www-<version>.zip     — www/ 全量打包(不含update包自身)
  out_dir/version.json          — 版本清单 {version, zip, files:[{path,size,sha256}], built_at}
部署: 把两个文件传到更新服务器目录(如腾讯云 C:\\hermes-update\\hermes-update\\)
"""
import hashlib
import json
import os
import sys
import zipfile

def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def build(version, www_dir, out_dir):
    www_dir = os.path.abspath(www_dir)
    if not os.path.isdir(www_dir):
        print(f"❌ www目录不存在: {www_dir}")
        sys.exit(1)
    os.makedirs(out_dir, exist_ok=True)

    zip_name = f"www-{version}.zip"
    zip_path = os.path.join(out_dir, zip_name)

    files = []
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, names in os.walk(www_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for name in names:
                full = os.path.join(root, name)
                rel = os.path.relpath(full, www_dir).replace('\\', '/')
                zf.write(full, rel)
                files.append({
                    'path': rel,
                    'size': os.path.getsize(full),
                    'sha256': sha256_file(full),
                })

    manifest = {
        'version': version,
        'zip': f'/hermes-update/{zip_name}',
        'built_at': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'files': files,
        'note': '御衡 Web资源热更新包',
    }
    vj_path = os.path.join(out_dir, 'version.json')
    with open(vj_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"✅ 打包完成: {zip_name} ({os.path.getsize(zip_path)/1024:.1f} KB, {len(files)} 文件)")
    print(f"✅ 清单: {vj_path}")
    print(f"   部署到服务器后URL: http://<server>:8401/hermes-update/version.json")
    print(f"   记得同步更新 UpdateManager.BUNDLED_WWW_VERSION 和 dashboard.html 的 HERMES_WWW_VERSION")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    version = sys.argv[1]
    www_dir = sys.argv[2] if len(sys.argv) > 2 else 'www'
    out_dir = sys.argv[3] if len(sys.argv) > 3 else '../hermes-update-publish'
    build(version, www_dir, out_dir)
