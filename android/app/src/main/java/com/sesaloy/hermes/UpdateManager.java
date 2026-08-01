package com.sesaloy.hermes;

import android.content.Context;
import android.util.Log;

import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * 御衡 Web资源热更新引擎。
 *
 * 机制:
 *   1. APP启动时(或手动)请求更新服务器 /hermes-update/version.json
 *   2. 若远端版本 != 当前内置版本, 下载 www-<version>.zip 并解压到 filesDir/hermes-www/<version>/
 *   3. WebView 通过 shouldInterceptRequest 优先从 filesDir 提供页面资源
 *   4. 下次启动沿用已更新版本, 无需重新安装APK
 *
 * 原生代码(Java)改动不在此热更新范围, 需重新打包APK。
 */
public class UpdateManager {

    private static final String TAG = "UpdateManager";

    /** 更新服务器根地址(腾讯云) — 可被JS桥覆盖 */
    public static volatile String UPDATE_SERVER = "http://49.234.196.103:8401";
    public static final String UPDATE_PATH = "/hermes-update/version.json";

    /** APK内置的www资源版本(与www打包时保持一致) */
    public static final String BUNDLED_WWW_VERSION = "1.5";

    private static final String WWW_ROOT = "hermes-www";
    private static final String CURRENT_VERSION_FILE = "current-version.txt";
    private static final int CONNECT_TIMEOUT_MS = 8000;
    private static final int READ_TIMEOUT_MS = 20000;

    public interface UpdateListener {
        /** result: "none" | "updated" | "failed" | "server_error"; newVersion 新版本号 */
        void onUpdateCheckDone(String result, String newVersion, String message);
    }

    /** 当前生效的更新目录(有热更新时返回, 否则null → 用内置assets) */
    public static File getActiveWebDir(Context context) {
        File root = new File(context.getFilesDir(), WWW_ROOT);
        if (!root.exists()) return null;
        String cur = readCurrentVersion(root);
        if (cur == null || cur.isEmpty()) return null;
        File dir = new File(root, cur);
        return dir.exists() && dir.isDirectory() ? dir : null;
    }

    public static String getActiveVersion(Context context) {
        File root = new File(context.getFilesDir(), WWW_ROOT);
        return readCurrentVersion(root);
    }

    /** 异步检查更新 (非阻塞, 后台线程) */
    public static void checkAndApplyAsync(final Context context, final UpdateListener listener) {
        Thread t = new Thread(() -> {
            String result = "none";
            String newVersion = null;
            String message = "";
            try {
                String baseUrl = UPDATE_SERVER.trim();
                URL u = new URL(baseUrl + UPDATE_PATH + "?from=" + BUNDLED_WWW_VERSION);
                HttpURLConnection conn = (HttpURLConnection) u.openConnection();
                conn.setConnectTimeout(CONNECT_TIMEOUT_MS);
                conn.setReadTimeout(READ_TIMEOUT_MS);
                conn.setRequestMethod("GET");
                int code = conn.getResponseCode();
                if (code != 200) {
                    result = "server_error";
                    message = "更新服务器响应 " + code;
                } else {
                    InputStream is = conn.getInputStream();
                    byte[] buf = new byte[4096];
                    java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream();
                    int n;
                    while ((n = is.read(buf)) != -1) bos.write(buf, 0, n);
                    is.close();
                    JSONObject j = new JSONObject(bos.toString("UTF-8"));
                    String remote = j.optString("version", "");
                    newVersion = remote;
                    if (remote == null || remote.isEmpty() || remote.equals(BUNDLED_WWW_VERSION)) {
                        result = "none";
                        message = "已是最新版本 v" + BUNDLED_WWW_VERSION;
                    } else {
                        // 下载并解压
                        String zipUrl = j.optString("zip", baseUrl + "/hermes-update/www-" + remote + ".zip");
                        boolean ok = downloadAndApply(context, zipUrl, remote);
                        if (ok) {
                            result = "updated";
                            message = "已更新到 v" + remote;
                        } else {
                            result = "failed";
                            message = "更新下载失败";
                        }
                    }
                }
                conn.disconnect();
            } catch (Exception e) {
                result = "server_error";
                message = "更新检查失败: " + e.getMessage();
                Log.w(TAG, "update check failed", e);
            }
            if (listener != null) {
                final String r = result, v = newVersion, m = message;
                android.os.Handler h = new android.os.Handler(android.os.Looper.getMainLooper());
                h.post(() -> listener.onUpdateCheckDone(r, v, m));
            }
        });
        t.setDaemon(true);
        t.start();
    }

    private static boolean downloadAndApply(Context context, String zipUrl, String version) throws IOException {
        File root = new File(context.getFilesDir(), WWW_ROOT);
        if (!root.exists() && !root.mkdirs()) return false;
        File targetDir = new File(root, version);
        if (targetDir.exists()) {
            // 已存在该版本 → 直接激活
            writeCurrentVersion(root, version);
            return true;
        }
        File tmpZip = new File(context.getCacheDir(), "hermes-update-" + version + ".zip");
        HttpURLConnection conn = (HttpURLConnection) new URL(zipUrl).openConnection();
        conn.setConnectTimeout(CONNECT_TIMEOUT_MS);
        conn.setReadTimeout(READ_TIMEOUT_MS);
        int code = conn.getResponseCode();
        if (code != 200) {
            conn.disconnect();
            return false;
        }
        try (InputStream in = conn.getInputStream(); FileOutputStream out = new FileOutputStream(tmpZip)) {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) != -1) out.write(buf, 0, n);
        }
        conn.disconnect();

        if (!unzip(tmpZip, targetDir)) {
            tmpZip.delete();
            return false;
        }
        tmpZip.delete();
        writeCurrentVersion(root, version);
        return true;
    }

    /** 安全解压(防zip-slip) */
    private static boolean unzip(File zipFile, File outDir) {
        try (ZipInputStream zis = new ZipInputStream(new FileInputStream(zipFile))) {
            ZipEntry entry;
            byte[] buf = new byte[8192];
            while ((entry = zis.getNextEntry()) != null) {
                String name = entry.getName();
                // 防路径穿越
                File dest = new File(outDir, name);
                String destPath = dest.getCanonicalPath();
                String outPath = outDir.getCanonicalPath();
                if (!destPath.startsWith(outPath + File.separator) && !destPath.equals(outPath)) {
                    Log.w(TAG, "blocked zip entry: " + name);
                    continue;
                }
                if (entry.isDirectory()) {
                    dest.mkdirs();
                } else {
                    File parent = dest.getParentFile();
                    if (parent != null) parent.mkdirs();
                    try (FileOutputStream fos = new FileOutputStream(dest)) {
                        int n;
                        while ((n = zis.read(buf)) != -1) fos.write(buf, 0, n);
                    }
                }
                zis.closeEntry();
            }
            return true;
        } catch (Exception e) {
            Log.w(TAG, "unzip failed", e);
            return false;
        }
    }

    private static String readCurrentVersion(File root) {
        File f = new File(root, CURRENT_VERSION_FILE);
        if (!f.exists()) return null;
        try (FileInputStream fis = new FileInputStream(f)) {
            byte[] buf = new byte[64];
            int n = fis.read(buf);
            return n > 0 ? new String(buf, 0, n, StandardCharsets.UTF_8).trim() : null;
        } catch (Exception e) {
            return null;
        }
    }

    private static void writeCurrentVersion(File root, String version) throws IOException {
        File f = new File(root, CURRENT_VERSION_FILE);
        try (FileOutputStream fos = new FileOutputStream(f)) {
            fos.write(version.getBytes(StandardCharsets.UTF_8));
        }
    }
}
