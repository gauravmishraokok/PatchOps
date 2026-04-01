#!/usr/bin/env python3
"""
Simple HTTP server to serve the PatchOps Security Terminal frontend
"""

import os
import sys
import json
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser

class TerminalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Serve the main page
        if parsed_path.path == '/' or parsed_path.path == '':
            self.path = '/index.html'
        
        # API endpoint to get real backend status
        elif parsed_path.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Simulate real backend status
            status = {
                'status': 'ready',
                'last_analysis': {
                    'vulnerabilities_found': 5,
                    'vulnerabilities_fixed': 5,
                    'success_rate': 100,
                    'timestamp': time.time()
                }
            }
            
            self.wfile.write(json.dumps(status).encode())
            return
        
        # API endpoint to trigger real analysis
        elif parsed_path.path == '/api/analyze':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Start real analysis in background
            def run_analysis():
                try:
                    # Change to parent directory and run the real analysis
                    os.chdir('..')
                    from test_red_and_blue import run_local_tests
                    run_local_tests()
                except Exception as e:
                    print(f"Analysis failed: {e}")
            
            # Run analysis in background thread
            analysis_thread = threading.Thread(target=run_analysis)
            analysis_thread.daemon = True
            analysis_thread.start()
            
            response = {'status': 'started', 'message': 'Security analysis initiated...'}
            self.wfile.write(json.dumps(response).encode())
            return
        
        return super().do_GET()
    
    def log_message(self, format, *args):
        # Custom logging to match terminal theme
        message = format % args
        print(f"[SERVER] {message}")

def main():
    port = 8080
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  <span style="color: #00ffff;">PatchOps Security Terminal Server</span>                    ║
║  <span style="color: #888;">Starting on http://localhost:{port}</span>                        ║
║                                                              ║
║  <span style="color: #00ff00;">✅ Frontend Ready</span>                                        ║
║  <span style="color: #ffff00;">⚠️  Backend Integration Available</span>                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    server = HTTPServer(('localhost', port), TerminalHandler)
    
    # Open browser automatically
    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        print(f"[SERVER] Listening on port {port}...")
        print("[SERVER] Press Ctrl+C to stop the server")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    main()
