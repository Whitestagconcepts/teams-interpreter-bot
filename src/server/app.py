#!/usr/bin/env python3
"""
Flask server for the Teams Interpreter Bot

This module provides a Flask web server to handle incoming requests
from Microsoft Teams and manage the bot's interactions.
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Flask imports
from flask import Flask, request, Response, jsonify

# Bot Framework imports
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter, BotTelemetryClient
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity

# Import our bot components
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.bot.interpreter_bot import InterpreterBot
from src.asr.whisper_asr import WhisperASR
from src.translation.nllb_translator import NLLBTranslator
from src.tts.piper_tts import PiperTTS

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Get configuration paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"
MODELS_DIR = BASE_DIR / "models"

# Set a flag to indicate if the bot is ready
bot_ready = False

# Load model config
try:
    with open(CONFIG_DIR / "model_config.json", "r", encoding="utf-8") as f:
        model_config = json.load(f)
except Exception as e:
    logger.error(f"Failed to load model config: {e}")
    model_config = {
        "asr": {"model_path": str(MODELS_DIR / "asr" / "ggml-tiny.en.bin"), "languages": {}},
        "translation": {"model_path": "", "language_codes": {}},
        "tts": {"voices": {}}
    }

# Initialize the bot components
try:
    # Initialize ASR (Speech Recognition)
    asr = WhisperASR(
        model_path=model_config["asr"]["model_path"],
        language_map=model_config["asr"].get("languages", {})
    )
    
    # Initialize Translator
    translator = NLLBTranslator(
        model_path=model_config["translation"]["model_path"],
        language_code_map=model_config["translation"].get("language_codes", {})
    )
    
    # Initialize TTS (Text-to-Speech)
    tts = PiperTTS(
        voice_map=model_config["tts"].get("voices", {})
    )
    
    # Initialize the bot with simpler components for testing
    BOT = {
        "user_languages": {},
        "active_meetings": {}
    }
    
    bot_ready = True
    logger.info("Bot components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bot components: {e}")
    BOT = None

# Define routes
@app.route("/", methods=["GET"])
def index():
    """Health check endpoint"""
    return jsonify({
        "status": "ok" if bot_ready else "initializing",
        "version": "1.0.0",
        "name": "Teams Interpreter Bot"
    })

@app.route("/api/messages", methods=["POST"])
def messages():
    """Main bot endpoint for Teams messages"""
    if not bot_ready:
        return jsonify({"error": "Bot is still initializing"}), 503
        
    if "application/json" in request.headers.get("Content-Type", ""):
        body = request.json
    else:
        return Response(status=415)  # Unsupported Media Type
    
    # Just echo the message back for testing
    try:
        message = body.get("text", "No message")
        language = body.get("language", "en-US")
        
        # Translate if needed
        if language != "en-US":
            translated = translator.translate(message, language, "en-US")
            response = {
                "original": message,
                "translated": translated,
                "source_language": language,
                "target_language": "en-US"
            }
        else:
            # Try translating to Spanish
            translated = translator.translate(message, "en-US", "es-CO")
            response = {
                "original": message,
                "translated": translated,
                "source_language": "en-US",
                "target_language": "es-CO"
            }
            
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/status", methods=["GET"])
def status():
    """API endpoint to check bot status"""
    components = {
        "asr": asr is not None,
        "translator": translator is not None,
        "tts": tts is not None,
        "bot": bot_ready
    }
    
    return jsonify({
        "status": "running" if bot_ready else "initializing",
        "components": components,
        "active_meetings": len(BOT.get("active_meetings", {})),
        "users_with_language_preferences": len(BOT.get("user_languages", {}))
    })

# Run the Flask app
if __name__ == "__main__":
    try:
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 3978))
        
        logger.info(f"Starting Flask server on {host}:{port}")
        app.run(host=host, port=port, debug=os.getenv("FLASK_DEBUG", "False").lower() == "true")
    except Exception as e:
        logger.error(f"Error starting Flask server: {e}")
        sys.exit(1) 