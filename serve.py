"""
ローカル確認用サーバー。本番と同じく /menu のような拡張子なしURLで表示します。
使い方:  python serve.py   →  http://localhost:8080
"""
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        path = self.path.split("?")[0].split("#")[0]
        if path != "/" and "." not in os.path.basename(path):
            candidate = os.path.join(ROOT, path.strip("/") + ".html")
            if os.path.isfile(candidate):
                self.path = "/" + path.strip("/") + ".html"
            else:
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(os.path.join(ROOT, "404.html"), "rb") as f:
                    self.wfile.write(f.read())
                return
        return super().do_GET()

    def log_message(self, fmt, *args):
        pass


http.server.ThreadingHTTPServer.allow_reuse_address = True
with http.server.ThreadingHTTPServer(("", PORT), Handler) as httpd:
    print(f"http://localhost:{PORT}")
    httpd.serve_forever()
