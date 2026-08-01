# -*- coding: utf-8 -*-
"""御衡热更新静态服务器 — 端口8401, 根目录 C:\\hermes-update\\
用法: python serve_update.py [port]  (默认8401)
"""
import http.server
import os
import socketserver
import sys

ROOT = sys.argv[2] if len(sys.argv) > 2 else r"C:\hermes-update"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8401
BIND = "0.0.0.0"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        # CORS: 允许手机APP/浏览器跨域检查更新
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stdout.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))
        sys.stdout.flush()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    os.makedirs(ROOT, exist_ok=True)
    srv = ThreadedHTTPServer((BIND, PORT), Handler)
    print("御衡更新服务器 http://%s:%d  目录: %s" % (BIND, PORT, ROOT), flush=True)
    srv.serve_forever()
