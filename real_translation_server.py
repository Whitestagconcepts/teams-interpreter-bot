#!/usr/bin/env python3
"""
Real Translation Server for Teams Interpreter Bot

This server provides real translation functionality using our SimpleTranslator
implementation which can work either with transformers or fallback to an API.
"""

import http.server
import socketserver
import json
import logging
import sys
import os
from pathlib import Path

# Add project root to path
project_path = Path(__file__).resolve().parent
sys.path.append(str(project_path))

# Import our translator
from src.translation.simple_translator import SimpleTranslator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define port
PORT = 8080

# Initialize translator
translator = SimpleTranslator()

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
                "bot": "Teams Interpreter Bot",
                "translator_ready": True,
                "using_transformers": translator.using_transformers,
                "using_fallback": translator.using_fallback
            }
        # API status endpoint
        elif self.path == "/api/status":
            response = {
                "status": "running",
                "translator": True,
                "supported_languages": ["en-US", "es-CO", "ru-RU"],
                "using_transformers": translator.using_transformers,
                "using_fallback": translator.using_fallback
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
        try:
            # Add a timeout mechanism
            import threading
            import time
            
            translated = None
            translation_error = None
            is_done = False
            
            def translate_with_timeout():
                nonlocal translated, translation_error, is_done
                try:
                    # Perform actual translation
                    translated = translator.translate(text, language, target_language)
                except Exception as e:
                    logger.error(f"Translation error inside thread: {e}")
                    translation_error = str(e)
                finally:
                    is_done = True
            
            # Start translation in a separate thread
            translate_thread = threading.Thread(target=translate_with_timeout)
            translate_thread.daemon = True
            translate_thread.start()
            
            # Wait for up to 10 seconds
            timeout = 10  # seconds
            start_time = time.time()
            while not is_done and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            # Handle timeout
            if not is_done:
                logger.warning(f"Translation timed out after {timeout} seconds")
                translated = f"{text} [Translation timed out]"
            elif translation_error:
                logger.error(f"Translation error: {translation_error}")
                translated = f"{text} [Translation error: {translation_error}]"
            
            response = {
                "original": text,
                "translated": translated,
                "source_language": language,
                "target_language": target_language,
                "using_transformers": translator.using_transformers,
                "using_fallback": translator.using_fallback,
                "timed_out": not is_done
            }
            
            # Return the response
            self._set_headers()
            self.wfile.write(json.dumps(response).encode())
            logger.info(f"Translated to {target_language}: '{translated[:50]}...'")
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            self._set_headers(status=500)
            self.wfile.write(json.dumps({
                "error": f"Translation failed: {str(e)}",
                "original": text
            }).encode())

def run_server():
    """Start the HTTP server"""
    try:
        # Allow socket reuse to prevent "Address already in use" errors
        socketserver.TCPServer.allow_reuse_address = True
        
        # Create the server - bind to all interfaces
        server = socketserver.TCPServer(("0.0.0.0", PORT), BotRequestHandler)
        
        logger.info(f"Starting real translation server on port {PORT}")
        logger.info(f"Server URL: http://localhost:{PORT}")
        logger.info(f"Translator using transformers: {translator.using_transformers}")
        logger.info(f"Translator using fallback: {translator.using_fallback}")
        
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
    print(f"Starting real translation server on port {PORT}...")
    print(f"Press Ctrl+C to stop the server")
    run_server() 