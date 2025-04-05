#!/usr/bin/env python3
"""
Teams Bot Calling Handler

This module handles incoming call notifications and manages the media sessions
for real-time interpretation during Teams calls.
"""

import os
import sys
import logging
import json
import requests
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timedelta
import traceback
from dotenv import load_dotenv

# Add project root to path
project_path = Path(__file__).resolve().parent
sys.path.append(str(project_path))

# Import our existing translation components
from src.tts.simple_tts import SimpleTTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Microsoft Graph API for calling
MS_GRAPH_API = "https://graph.microsoft.com/v1.0"
APP_ID = os.getenv("MICROSOFT_APP_ID")
APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD")

# Translation service URL
TRANSLATION_SERVICE_URL = os.getenv("TRANSLATION_SERVICE_URL", "http://localhost:8080")

# Initialize TTS component
tts_engine = SimpleTTS()

class CallHandler:
    """Handler for Teams calls"""

    def __init__(self):
        self.token = None
        self.token_expires = datetime.now()
        self.active_calls = {}
        
    async def get_token(self):
        """Get an authentication token for Microsoft Graph API"""
        if self.token and self.token_expires > datetime.now():
            return self.token
            
        try:
            # Token endpoint
            token_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/token"
            
            # Request body
            data = {
                'grant_type': 'client_credentials',
                'client_id': APP_ID,
                'client_secret': APP_PASSWORD,
                'scope': 'https://graph.microsoft.com/.default'
            }
            
            # Make request
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('access_token')
                expires_in = result.get('expires_in', 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                return self.token
            else:
                logger.error(f"Failed to get token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting token: {e}")
            logger.error(traceback.format_exc())
            return None
    
    async def answer_call(self, call_id):
        """Answer an incoming call"""
        try:
            token = await self.get_token()
            if not token:
                logger.error("Failed to get token for answering call")
                return False
                
            # Endpoint for answering call
            url = f"{MS_GRAPH_API}/communications/calls/{call_id}/answer"
            
            # Headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Request body for answering - accept audio only initially
            data = {
                "acceptedModalities": ["audio"],
                "mediaConfig": {
                    "@odata.type": "#microsoft.graph.serviceHostedMediaConfig",
                    "preFetchMedia": [
                        {
                            "uri": "https://stagsigns.net/teams-bot/static/welcome.wav",
                            "resourceId": "welcome"
                        }
                    ]
                }
            }
            
            # Make request
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 202]:
                logger.info(f"Call {call_id} answered successfully")
                
                # Play welcome message
                await self.play_prompt(call_id, "welcome")
                
                # Start monitoring call for speech
                self.active_calls[call_id] = {
                    "start_time": datetime.now(),
                    "language": "en-US",  # Default language
                    "target_language": "es-CO"  # Default target language
                }
                
                # Start speech recognition (would be implemented in a real system)
                asyncio.create_task(self.monitor_call_audio(call_id))
                
                return True
            else:
                logger.error(f"Failed to answer call: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error answering call: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def play_prompt(self, call_id, resource_id):
        """Play a prompt on a call"""
        try:
            token = await self.get_token()
            if not token:
                logger.error("Failed to get token for playing prompt")
                return False
                
            # Endpoint for playing prompt
            url = f"{MS_GRAPH_API}/communications/calls/{call_id}/playPrompt"
            
            # Headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Request body
            data = {
                "prompts": [
                    {
                        "@odata.type": "#microsoft.graph.mediaPrompt",
                        "mediaInfo": {
                            "@odata.type": "#microsoft.graph.mediaInfo",
                            "resourceId": resource_id,
                            "uri": None
                        }
                    }
                ]
            }
            
            # Make request
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 202]:
                logger.info(f"Prompt played successfully on call {call_id}")
                return True
            else:
                logger.error(f"Failed to play prompt: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error playing prompt: {e}")
            logger.error(traceback.format_exc())
            return False
    
    async def monitor_call_audio(self, call_id):
        """Monitor call audio for speech to translate
        
        In a real implementation, this would connect to the Teams real-time media API
        to receive audio streams and send them for speech recognition.
        """
        try:
            # In a real implementation, this would use WebRTC or the Teams media API
            # to access the audio stream and send it for speech recognition
            
            # For this demo, we'll simulate receiving periodic speech segments
            while call_id in self.active_calls:
                # Simulate waiting for speech (in a real bot, this would be event-driven)
                await asyncio.sleep(15)
                
                # Simulated recognized speech
                text = "This is a simulated speech segment that would be recognized from the call"
                source_language = self.active_calls[call_id]["language"]
                target_language = self.active_calls[call_id]["target_language"]
                
                # Translate the speech
                translated = await self.translate_text(text, source_language, target_language)
                
                # Generate speech from translation
                audio_path = await self.generate_speech(translated, target_language)
                
                # In a real implementation, the audio would be played back into the call
                logger.info(f"Would play translated audio: {translated}")
                
        except Exception as e:
            logger.error(f"Error monitoring call audio: {e}")
            logger.error(traceback.format_exc())
        finally:
            # Cleanup when the task ends
            if call_id in self.active_calls:
                del self.active_calls[call_id]
    
    async def translate_text(self, text, source_language, target_language):
        """Translate text using our translation service"""
        try:
            # Prepare the request
            url = f"{TRANSLATION_SERVICE_URL}/api/messages"
            data = {
                "text": text,
                "language": source_language,
                "target_language": target_language
            }
            
            # Send the request
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("translated", text)
            else:
                logger.error(f"Translation error: {response.text}")
                return f"[Translation failed] {text}"
                
        except Exception as e:
            logger.error(f"Error translating: {e}")
            return f"[Translation error] {text}"
    
    async def generate_speech(self, text, language):
        """Generate speech from text"""
        try:
            if not tts_engine.ready:
                logger.warning("TTS engine not ready")
                return None
                
            # Use the TTS engine to generate speech
            audio_path = tts_engine.text_to_speech(text, language)
            return audio_path
                
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return None
            
    async def end_call(self, call_id):
        """End an active call"""
        try:
            token = await self.get_token()
            if not token:
                logger.error("Failed to get token for ending call")
                return False
                
            # Endpoint for ending call
            url = f"{MS_GRAPH_API}/communications/calls/{call_id}"
            
            # Headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Make request
            response = requests.delete(url, headers=headers)
            
            if response.status_code in [204, 202]:
                logger.info(f"Call {call_id} ended successfully")
                
                # Clean up
                if call_id in self.active_calls:
                    del self.active_calls[call_id]
                    
                return True
            else:
                logger.error(f"Failed to end call: {response.status_code}, {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            logger.error(traceback.format_exc())
            return False

# Create a singleton handler
call_handler = CallHandler()

# Function to process an incoming call notification
async def process_call_notification(notification):
    """Process a call notification from Teams"""
    try:
        # Parse the notification
        notification_type = notification.get("@odata.type", "")
        resource = notification.get("resource", {})
        
        # Check for incoming call
        if notification_type == "#microsoft.graph.commsNotifications" and "value" in notification:
            for item in notification["value"]:
                change_type = item.get("changeType", "")
                resource = item.get("resource", {})
                
                if change_type == "created" and "call" in resource:
                    call_id = resource["call"]["id"]
                    logger.info(f"Incoming call notification received: {call_id}")
                    
                    # Answer the call
                    await call_handler.answer_call(call_id)
                    
        # Process other notification types as needed
        
    except Exception as e:
        logger.error(f"Error processing call notification: {e}")
        logger.error(traceback.format_exc())

# Function to process an incoming call
async def handle_call_request(request_data):
    """Handle an incoming call request from the webhook"""
    try:
        # Parse the webhook data
        data = json.loads(request_data)
        
        # Process based on notification type
        await process_call_notification(data)
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling call request: {e}")
        logger.error(traceback.format_exc())
        return False

# For testing the calling integration
if __name__ == "__main__":
    # This would be used for direct testing of call handling
    print("This module is designed to be imported by the main Flask application.")
    print("It provides call handling capabilities for the Teams Interpreter Bot.") 