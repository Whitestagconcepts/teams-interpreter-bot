#!/usr/bin/env python3
"""
Translation-only Bot Server using Python's built-in http.server

This is a simplified version that only includes translation functionality
for easier testing and debugging.
"""

import http.server
import socketserver
import json
import os
import sys
import logging
from pathlib import Path
import traceback

# Add project root to path
project_path = Path(__file__).resolve().parent
sys.path.append(str(project_path))

# Import translation components only
from src.translation.nllb_translator import NLLBTranslator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define port (use a different port to avoid conflicts)
PORT = 5000

# Initialize translation engine only
translator = None
try:
    translator = NLLBTranslator("")  # Model path not needed for MarianMT
    logger.info("Translator initialized successfully")
    
    # Test the translator with a simple sentence
    test_translation = translator.translate("Hello world", "en-US", "es-CO")
    logger.info(f"Test translation: 'Hello world' -> '{test_translation}'")
except Exception as e:
    logger.error(f"Failed to initialize translator: {e}")
    logger.error(traceback.format_exc())

# Custom request handler
class BotRequestHandler(http.server.BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info("%s - %s" % (self.address_string(), format % args))
    
    def _set_headers(self, content_type="application/json", status=200):
        """Set response headers"""
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def _handle_error(self, status, message):
        """Handle errors with proper response"""
        self._set_headers(status=status)
        response = {
            "error": message,
            "status": "error"
        }
        self.wfile.write(json.dumps(response).encode())
    
    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            # Health check endpoint
            if self.path == "/" or self.path == "/api/health":
                self._set_headers()
                response = {
                    "status": "ok",
                    "bot": "Teams Interpreter Bot (Translation Only)",
                    "translator_ready": translator is not None
                }
            # API status endpoint
            elif self.path == "/api/status":
                self._set_headers()
                response = {
                    "status": "running",
                    "translator": translator is not None,
                    "supported_languages": ["en-US", "es-CO", "ru-RU"]
                }
            else:
                return self._handle_error(404, "Endpoint not found")
            
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            logger.error(traceback.format_exc())
            self._handle_error(500, f"Internal server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            
            if content_length == 0:
                return self._handle_error(400, "Empty request body")
            
            # Read and parse the request body
            try:
                post_data = self.rfile.read(content_length)
                request_body = json.loads(post_data.decode('utf-8'))
            except json.JSONDecodeError:
                return self._handle_error(400, "Invalid JSON")
            
            # Handle messages endpoint
            if self.path == "/api/messages":
                self._handle_message(request_body)
            else:
                return self._handle_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            logger.error(traceback.format_exc())
            self._handle_error(500, f"Internal server error: {str(e)}")
    
    def _handle_message(self, request_body):
        """Process a message request"""
        # Extract message and language
        text = request_body.get("text", "")
        language = request_body.get("language", "en-US")
        target_language = request_body.get("target_language")
        
        if not text:
            return self._handle_error(400, "Missing text in request")
        
        logger.info(f"Received message: '{text[:50]}...' in {language}")
        
        # If target language not specified, use a default based on source language
        if not target_language:
            if language == "en-US":
                target_language = "es-CO"
            else:
                target_language = "en-US"
        
        # If source and target are the same, pick a different target
        if target_language == language:
            if language == "en-US":
                target_language = "es-CO"
            else:
                target_language = "en-US"
        
        # Create the response object
        response = {
            "original": text,
            "source_language": language,
            "target_language": target_language
        }
        
        # Perform translation if translator is available
        if translator:
            try:
                translated = translator.translate(text, language, target_language)
                response["translated"] = translated
                logger.info(f"Translated to {target_language}: '{translated[:50]}...'")
            except Exception as e:
                logger.error(f"Translation error: {e}")
                response["error"] = f"Translation failed: {str(e)}"
                response["translated"] = f"{text} [Translation error]"
        else:
            response["error"] = "Translator not available"
            response["translated"] = f"{text} [Translator offline]"
        
        # Return the response
        self._set_headers()
        self.wfile.write(json.dumps(response).encode())

def run_server():
    """Start the HTTP server"""
    try:
        # Allow socket reuse to prevent "Address already in use" errors
        socketserver.TCPServer.allow_reuse_address = True
        
        # Create the server
        server = socketserver.TCPServer(("", PORT), BotRequestHandler)
        
        logger.info(f"Starting translation-only bot server on port {PORT}")
        logger.info(f"Server URL: http://localhost:{PORT}")
        
        # Serve until interrupted
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
    finally:
        if 'server' in locals():
            server.server_close()
            logger.info("Server closed")

if __name__ == "__main__":
    run_server() 