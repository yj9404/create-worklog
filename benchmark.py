import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')
    def do_POST(self):
        self.send_response(201)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"id": "123"}')
    def log_message(self, format, *args):
        pass # suppress logs

def run_server():
    server = HTTPServer(('localhost', 8080), DummyHandler)
    server.serve_forever()

if __name__ == '__main__':
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1) # wait for server to start

    N = 100

    # Without session
    start = time.time()
    for _ in range(N):
        requests.get('http://localhost:8080/')
    duration_no_session = time.time() - start
    print(f"Without session: {duration_no_session:.4f} seconds for {N} requests")

    # With session
    session = requests.Session()
    start = time.time()
    for _ in range(N):
        session.get('http://localhost:8080/')
    duration_session = time.time() - start
    print(f"With session: {duration_session:.4f} seconds for {N} requests")
    print(f"Improvement: {duration_no_session / duration_session:.2f}x faster")
