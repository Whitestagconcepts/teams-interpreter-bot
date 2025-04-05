#!/usr/bin/env python3
"""
Translation and TTS Server for Teams Interpreter Bot

This server provides both translation and text-to-speech capabilities,
using our simplified implementations for reliability.
"""

import http.server
import socketserver
import json
import logging
import sys
import os
import base64
import time
import random
from pathlib import Path

# Add project root to path
project_path = Path(__file__).resolve().parent
sys.path.append(str(project_path))

# Import our components
from src.tts.simple_tts import SimpleTTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define port
PORT = 8080

# Simple mock translations for testing
MOCK_TRANSLATIONS = {
    "en": {
        "Hello": "Hola",
        "world": "mundo",
        "How are you": "Cómo estás",
        "Good morning": "Buenos días",
        "Thank you": "Gracias",
        "Goodbye": "Adiós",
        "What is your name": "Cómo te llamas",
        "My name is": "Me llamo",
        "Welcome": "Bienvenido"
    },
    "es": {
        "Hola": "Hello",
        "mundo": "world",
        "Cómo estás": "How are you",
        "Buenos días": "Good morning",
        "Gracias": "Thank you",
        "Adiós": "Goodbye",
        "Cómo te llamas": "What is your name",
        "Me llamo": "My name is",
        "Bienvenido": "Welcome"
    },
    "ru": {
        "Привет": "Hello",
        "мир": "world",
        "Как дела": "How are you",
        "Доброе утро": "Good morning",
        "Спасибо": "Thank you",
        "До свидания": "Goodbye"
    }
}

# Simple mock translator using dictionary lookup
class MockTranslator:
    def __init__(self):
        self.language_code_map = {
            "en-US": "en",
            "ru-RU": "ru", 
            "es-CO": "es"
        }
        logger.info("Mock translator initialized")
    
    def translate(self, text, source_lang, target_lang):
        """Simple mock translation with basic word replacements"""
        src_lang = self.language_code_map.get(source_lang, source_lang.split('-')[0])
        tgt_lang = self.language_code_map.get(target_lang, target_lang.split('-')[0])
        
        # If source and target are the same, return original
        if src_lang == tgt_lang:
            return text
            
        # Add a slight delay to simulate processing time
        time.sleep(0.1)
        
        # Simple dictionary-based lookup for common phrases
        if src_lang in MOCK_TRANSLATIONS:
            for phrase, translation in MOCK_TRANSLATIONS[src_lang].items():
                if phrase.lower() in text.lower():
                    text = text.replace(phrase, translation)
        
        # If no lookup matches, add a prefix
        if text == "":
            return f"[{tgt_lang}] Empty message"
            
        # Check if we found a translation
        for phrase in MOCK_TRANSLATIONS.get(src_lang, {}).values():
            if phrase in text:
                # We found a translation, so return as is
                return text
                
        # No translation found in our dictionary, so add a prefix
        return f"[{tgt_lang}] {text}"

# Initialize our components
translator = MockTranslator()
tts_engine = SimpleTTS()

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
                "tts_ready": tts_engine.ready
            }
        # API status endpoint
        elif self.path == "/api/status":
            response = {
                "status": "running",
                "translator": True,
                "tts": tts_engine.ready,
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
        
        # Handle different API endpoints
        if self.path == "/api/messages":
            self._handle_message(request_body)
        elif self.path == "/api/tts":
            self._handle_tts(request_body)
        else:
            self._set_headers(status=404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode())
    
    def _handle_message(self, request_body):
        """Process a message request for translation"""
        # Extract message and language
        text = request_body.get("text", "")
        language = request_body.get("language", "en-US")
        target_language = request_body.get("target_language")
        generate_audio = request_body.get("generate_audio", False)
        
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
        
        # Perform translation
        translated = translator.translate(text, language, target_language)
        
        # Create the response object
        response = {
            "original": text,
            "translated": translated,
            "source_language": language,
            "target_language": target_language
        }
        
        # Generate audio if requested and TTS is available
        if generate_audio and tts_engine.ready:
            try:
                # Generate speech for the translation
                audio_path = tts_engine.text_to_speech(translated, target_language)
                
                if audio_path and os.path.exists(audio_path):
                    # Read the audio file and encode as base64
                    with open(audio_path, "rb") as audio_file:
                        audio_data = audio_file.read()
                        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                        
                    # Add audio to the response
                    response["audio"] = audio_base64
                    response["audio_format"] = "wav"
                    
                    # Clean up the temporary file
                    try:
                        os.remove(audio_path)
                    except:
                        pass
                else:
                    logger.warning("Failed to generate audio")
                    response["audio_error"] = "Failed to generate audio"
            except Exception as e:
                logger.error(f"Error generating audio: {e}")
                response["audio_error"] = str(e)
        
        # Return the response
        self._set_headers()
        self.wfile.write(json.dumps(response).encode())
        logger.info(f"Translated to {target_language}: '{translated[:50]}...'")
    
    def _handle_tts(self, request_body):
        """Process a text-to-speech request"""
        # Extract text and language
        text = request_body.get("text", "")
        language = request_body.get("language", "en-US")
        
        if not text:
            self._set_headers(status=400)
            self.wfile.write(json.dumps({"error": "Missing text in request"}).encode())
            return
        
        if not tts_engine.ready:
            self._set_headers(status=503)
            self.wfile.write(json.dumps({"error": "TTS engine not available"}).encode())
            return
            
        logger.info(f"TTS request: '{text[:50]}...' in {language}")
        
        try:
            # Generate speech
            audio_path = tts_engine.text_to_speech(text, language)
            
            if audio_path and os.path.exists(audio_path):
                # Read the audio file and encode as base64
                with open(audio_path, "rb") as audio_file:
                    audio_data = audio_file.read()
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    
                # Create response
                response = {
                    "text": text,
                    "language": language,
                    "audio": audio_base64,
                    "audio_format": "wav"
                }
                
                # Clean up the temporary file
                try:
                    os.remove(audio_path)
                except:
                    pass
                    
                # Return the response
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())
                logger.info(f"TTS generated for {language}")
            else:
                self._set_headers(status=500)
                self.wfile.write(json.dumps({"error": "Failed to generate audio"}).encode())
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            self._set_headers(status=500)
            self.wfile.write(json.dumps({"error": f"TTS error: {str(e)}"}).encode())

def run_server():
    """Start the HTTP server"""
    try:
        # Allow socket reuse to prevent "Address already in use" errors
        socketserver.TCPServer.allow_reuse_address = True
        
        # Create the server - bind to all interfaces
        server = socketserver.TCPServer(("0.0.0.0", PORT), BotRequestHandler)
        
        logger.info(f"Starting Translation + TTS server on port {PORT}")
        logger.info(f"Server URL: http://localhost:{PORT}")
        logger.info(f"TTS engine ready: {tts_engine.ready}")
        
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
    print(f"Starting Translation + TTS server on port {PORT}...")
    print(f"Press Ctrl+C to stop the server")
    run_server() 