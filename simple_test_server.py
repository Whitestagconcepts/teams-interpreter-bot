#!/usr/bin/env python3
"""
Simple Test Server for Teams Interpreter Bot

This is a minimal server that just returns mock translations
for testing the server connection and API endpoints
"""

import http.server
import socketserver
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define port
PORT = 8080

# Simple mock translator
class MockTranslator:
    def __init__(self):
        self.language_code_map = {
            "en-US": "en",
            "ru-RU": "ru", 
            "es-CO": "es"
        }
        logger.info("Mock translator initialized")
    
    def translate(self, text, source_lang, target_lang):
        # Just add a prefix to indicate "translation"
        lang_code = self.language_code_map.get(target_lang, target_lang)
        return f"[{lang_code}] {text}"

# Initialize translator
translator = MockTranslator()

# Custom request handler
class BotRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        self._set_headers()
        
        # Health check endpoint
        if self.path == "/" or self.path == "/api/health":
            response = {
                "status": "ok",
                "bot": "Teams Interpreter Bot (Test Server)",
                "translator_ready": True
            }
        # API status endpoint
        elif self.path == "/api/status":
            response = {
                "status": "running",
                "translator": True,
                "supported_languages": ["en-US", "es-CO", "ru-RU"]
            }
        else:
            response = {
                "status": "error",
                "message": "Endpoint not found"
            }
            self._set_headers(status=404)
        
        self.wfile.write(json.dumps(response).encode())
        logger.info(f"GET {self.path} - {response['status']}")
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        
        if content_length == 0:
            self._set_headers(status=400)
            self.wfile.write(json.dumps({"error": "Empty request body"}).encode())
            return
        
        # Read and parse the request body
        try:
            post_data = self.rfile.read(content_length)
            request_body = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self._set_headers(status=400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return
        
        # Endpoint for messages
        if self.path == "/api/messages":
            self._handle_message(request_body)
        else:
            self._set_headers(status=404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
    
    def _handle_message(self, request_body):
        """Process a message request"""
        # Extract message and language
        text = request_body.get("text", "")
        language = request_body.get("language", "en-US")
        target_language = request_body.get("target_language")
        
        if not text:
            self._set_headers(status=400)
            self.wfile.write(json.dumps({"error": "Missing text in request"}).encode())
            return
        
        logger.info(f"Received message: '{text[:50]}...' in {language}")
        
        # If target language not specified, use a default based on source language
        if not target_language:
            if language == "en-US":
                target_language = "es-CO"
            else:
                target_language = "en-US"
        
        # Create the response object
        translated = translator.translate(text, language, target_language)
        response = {
            "original": text,
            "translated": translated,
            "source_language": language,
            "target_language": target_language
        }
        
        # Return the response
        self._set_headers()
        self.wfile.write(json.dumps(response).encode())
        logger.info(f"Translated to {target_language}: '{translated[:50]}...'")

def run_server():
    """Start the HTTP server"""
    try:
        # Allow socket reuse to prevent "Address already in use" errors
        socketserver.TCPServer.allow_reuse_address = True
        
        # Create the server - bind to all interfaces
        server = socketserver.TCPServer(("0.0.0.0", PORT), BotRequestHandler)
        
        logger.info(f"Starting test server on port {PORT}")
        logger.info(f"Server URL: http://localhost:{PORT}")
        
        # Serve until interrupted
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if 'server' in locals():
            server.server_close()
            logger.info("Server closed")

if __name__ == "__main__":
    print(f"Starting simple test server on port {PORT}...")
    print(f"Press Ctrl+C to stop the server")
    run_server() 