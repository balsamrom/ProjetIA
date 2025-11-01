#!/usr/bin/env python3
"""
Simple HTTP server to serve the admin dashboard
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Configuration
PORT = 8080
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    """Start the admin dashboard server"""
    print("🚀 Starting VogueVue Admin Dashboard Server...")
    print(f"📁 Serving directory: {DIRECTORY}")
    print(f"🌐 Server will be available at: http://localhost:{PORT}")
    print("📱 Admin Dashboard: http://localhost:8080/index.html")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully on port {PORT}")
            print("🔄 Press Ctrl+C to stop the server")
            print("=" * 50)
            
            # Automatically open the browser
            webbrowser.open(f'http://localhost:{PORT}/index.html')
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {PORT} is already in use")
            print(f"💡 Try using a different port or stop the service using port {PORT}")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
