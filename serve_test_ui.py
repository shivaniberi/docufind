"""
Simple HTTP server to serve the test UI
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8001
DOCUFIND_DIR = Path("/Users/vallabhnaik/Desktop/docufind")

class TestUIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/test':
            self.path = '/test_ui.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(DOCUFIND_DIR)
    
    with socketserver.TCPServer(("", PORT), TestUIHandler) as httpd:
        print(f"✅ Test UI Server running on http://127.0.0.1:{PORT}")
        print(f"📖 Open browser at: http://127.0.0.1:{PORT}/test_ui.html")
        print(f"\n📝 FastMCP Server is running on http://127.0.0.1:8000")
        print(f"   Test tools in the UI at http://127.0.0.1:{PORT}\n")
        httpd.serve_forever()
