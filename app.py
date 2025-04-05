#!/usr/bin/env python3
"""
Web Server for Teams Bot

This is the entry point for the Teams Bot integration, providing
HTTP endpoints that Microsoft Teams can communicate with.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, send_from_directory, jsonify

# Add project root to path for local imports
project_path = Path(__file__).resolve().parent
sys.path.append(str(project_path))

# Import our Teams Bot components
from teams_bot import process_activity
from calling_handler import handle_call_request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """Handle root endpoint for health checks"""
    return Response(
        "Teams Interpreter Bot is up and running!",
        status=200,
        mimetype="text/plain"
    )

@app.route("/api/messages", methods=["POST"])
async def messages():
    """Handle incoming messages from Teams"""
    if request.method == "POST":
        # Get the request body and headers
        request_body = await request.get_data()
        request_headers = dict(request.headers)
        
        # Process the activity
        await process_activity(request_body, request_headers)
        
        # Return a 200 response
        return Response(status=200)
    else:
        return Response(status=405)

@app.route("/api/calls", methods=["POST"])
async def calls():
    """Handle incoming call notifications from Teams"""
    if request.method == "POST":
        # Get the request body
        request_body = await request.get_data()
        
        # Process the call request
        success = await handle_call_request(request_body)
        
        if success:
            return Response(status=202)  # Accepted
        else:
            return Response(status=500)  # Internal Server Error
    else:
        return Response(status=405)  # Method Not Allowed

@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static files"""
    return send_from_directory(os.path.join(app.root_path, "static"), filename)

@app.route("/manifest.json", methods=["GET"])
def manifest():
    """Serve the Teams manifest file"""
    return send_from_directory(
        os.path.join(app.root_path, "static"), 
        "manifest.json",
        mimetype="application/json"
    )

@app.route("/.well-known/microsoft-bot-framework.json", methods=["GET"])
def bot_framework_config():
    """Serve the Bot Framework config file for verification"""
    app_id = os.getenv("MICROSOFT_APP_ID", "")
    
    if not app_id:
        logger.warning("Microsoft App ID not configured")
        
    config = {
        "apps": [
            {
                "appId": app_id,
                "appType": "Production"
            }
        ],
        "isCompliant": True
    }
    
    return jsonify(config)

# Create a welcome message audio file
def ensure_welcome_audio():
    """Ensure the welcome audio file exists"""
    from src.tts.simple_tts import SimpleTTS
    
    # Path to static directory
    static_dir = os.path.join(app.root_path, "static")
    os.makedirs(static_dir, exist_ok=True)
    
    # Check if welcome.wav exists
    welcome_path = os.path.join(static_dir, "welcome.wav")
    if not os.path.exists(welcome_path):
        try:
            # Create using TTS
            tts = SimpleTTS()
            if tts.ready:
                # Generate welcome message
                welcome_text = "Welcome to the Teams Interpreter Bot. I will translate the conversation for you."
                audio_path = tts.text_to_speech(welcome_text, "en-US")
                
                # Copy to static directory
                if audio_path and os.path.exists(audio_path):
                    import shutil
                    shutil.copy(audio_path, welcome_path)
                    logger.info(f"Created welcome audio file at {welcome_path}")
        except Exception as e:
            logger.error(f"Error creating welcome audio: {e}")

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 3978))
    
    # Ensure welcome audio exists
    ensure_welcome_audio()
    
    print(f"Starting Teams Interpreter Bot server on port {port}")
    print("Press Ctrl+C to quit")
    
    # Run the Flask app
    app.run(host="0.0.0.0", port=port) 