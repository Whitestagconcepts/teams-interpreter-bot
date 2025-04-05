#!/usr/bin/env python3
"""
Teams Bot Integration for the Interpreter Bot

This connects Microsoft Teams to our translation and TTS services.
"""

import os
import sys
import logging
import json
import requests
from pathlib import Path
import traceback
from dotenv import load_dotenv

# Bot Framework imports
from botbuilder.core import BotFrameworkAdapter, TurnContext, CardFactory
from botbuilder.core.teams import TeamsActivityHandler
from botbuilder.schema import Activity, ActivityTypes, Attachment, CardAction, HeroCard, ActionTypes
from botframework.connector.auth import MicrosoftAppCredentials

# Add project root to path for local imports
project_path = Path(__file__).resolve().parent
sys.path.append(str(project_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Bot credentials from environment variables
APP_ID = os.getenv("MICROSOFT_APP_ID", "")
APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD", "")

# Translation service details
TRANSLATION_SERVICE_URL = os.getenv("TRANSLATION_SERVICE_URL", "http://localhost:8080")

# Create the bot adapter with auth
adapter = BotFrameworkAdapter(
    app_id=APP_ID,
    app_password=APP_PASSWORD,
)

class TeamsInterpreterBot(TeamsActivityHandler):
    """Teams bot for translation and TTS"""
    
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages"""
        # Get the message text and sender language preference
        text = turn_context.activity.text
        sender_language = "en-US"  # Default language
        
        # Check if user has set a language preference
        # (In a real app, you would store these in a database)
        user_id = turn_context.activity.from_property.id
        
        logger.info(f"Message from {user_id}: {text[:50]}...")
        
        try:
            # Determine if this is a command
            if text.startswith("/"):
                await self._handle_command(turn_context, text)
            else:
                # Regular message to translate
                await self._process_translation(turn_context, text, sender_language)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())
            await turn_context.send_activity("Sorry, I encountered an error processing your message.")
    
    async def _handle_command(self, turn_context: TurnContext, text: str):
        """Handle bot commands"""
        command = text.lower().split()[0]
        
        if command == "/help":
            help_text = (
                "# Teams Interpreter Bot Help\n\n"
                "This bot can translate messages between languages and can join meetings to provide real-time interpretation.\n\n"
                "## Commands:\n"
                "- `/help` - Show this help message\n"
                "- `/languages` - Show supported languages\n"
                "- `/translate <text>` - Translate text\n"
                "- `/speak <text>` - Convert text to speech\n"
                "- `/call <meeting-link>` - Join a meeting (Coming soon)\n"
            )
            await turn_context.send_activity(help_text)
            
        elif command == "/languages":
            languages = "Supported languages:\n- English (en-US)\n- Spanish (es-CO)\n- Russian (ru-RU)"
            await turn_context.send_activity(languages)
            
        elif command == "/translate":
            # Extract the text to translate
            if len(text.split()) > 1:
                text_to_translate = text[len("/translate "):].strip()
                await self._process_translation(turn_context, text_to_translate, "en-US")
            else:
                await turn_context.send_activity("Please provide text to translate: `/translate <text>`")
                
        elif command == "/speak":
            # Extract the text to speak
            if len(text.split()) > 1:
                text_to_speak = text[len("/speak "):].strip()
                await self._process_tts(turn_context, text_to_speak, "en-US")
            else:
                await turn_context.send_activity("Please provide text to speak: `/speak <text>`")
                
        elif command == "/call":
            # Extract meeting link
            if len(text.split()) > 1:
                meeting_link = text[len("/call "):].strip()
                await turn_context.send_activity(f"Joining meeting capability is coming soon. Meeting link: {meeting_link}")
            else:
                await turn_context.send_activity("Please provide a meeting link: `/call <meeting-link>`")
                
        else:
            await turn_context.send_activity(f"Unknown command: {command}. Type `/help` for available commands.")
    
    async def _process_translation(self, turn_context: TurnContext, text: str, source_language: str):
        """Process a translation request"""
        # Use our translation service
        try:
            # Prepare the request
            url = f"{TRANSLATION_SERVICE_URL}/api/messages"
            data = {
                "text": text,
                "language": source_language,
                "generate_audio": True  # Include TTS
            }
            
            # Send the request to our service
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get("translated", "")
                target_language = result.get("target_language", "")
                
                # Send the translation back to Teams
                reply = f"**Original ({source_language})**: {text}\n\n"
                reply += f"**Translation ({target_language})**: {translated_text}"
                
                await turn_context.send_activity(reply)
                
                # If audio was generated, send that as well
                if "audio" in result:
                    # We would need to handle the audio file
                    # In a real app, you might upload this to blob storage
                    # and create a card with an audio player
                    await turn_context.send_activity("Audio translation is available but can't be played directly in Teams.")
            else:
                await turn_context.send_activity(f"Translation error: {response.text}")
                
        except Exception as e:
            logger.error(f"Translation service error: {e}")
            await turn_context.send_activity("Sorry, there was an error connecting to the translation service.")
    
    async def _process_tts(self, turn_context: TurnContext, text: str, language: str):
        """Process a text-to-speech request"""
        try:
            # Prepare the request
            url = f"{TRANSLATION_SERVICE_URL}/api/tts"
            data = {
                "text": text,
                "language": language
            }
            
            # Send the request to our service
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                await turn_context.send_activity(f"Generated speech for: {text}")
                await turn_context.send_activity("Audio is available but can't be played directly in Teams.")
            else:
                await turn_context.send_activity(f"Text-to-speech error: {response.text}")
                
        except Exception as e:
            logger.error(f"TTS service error: {e}")
            await turn_context.send_activity("Sorry, there was an error connecting to the TTS service.")

# Function to process incoming activities from the Adapter
async def process_activity(request_body, headers):
    """Process an incoming activity"""
    # Create a new activity from the request
    activity = Activity().deserialize(json.loads(request_body))
    auth_header = headers.get("Authorization", "")
    
    # Process the activity with the bot
    bot = TeamsInterpreterBot()
    
    # Use the adapter to process the activity
    async def turn_call(turn_context):
        await bot.on_turn(turn_context)
    
    await adapter.process_activity(activity, auth_header, turn_call)

# If running directly, this would be the entry point for a web server
if __name__ == "__main__":
    logger.info("This file should be imported by a web server, not run directly.")
    logger.info("Please set up a web server (like Flask) to receive requests from Microsoft Teams.") 