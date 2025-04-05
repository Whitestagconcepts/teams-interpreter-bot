#!/usr/bin/env python3
"""
Interpreter Bot for Microsoft Teams

This module provides the main bot class for handling Teams interactions
and managing real-time translation during meetings.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional

# Bot Framework imports
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    TurnContext,
    UserState,
)
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount, ConversationReference
from botbuilder.schema.teams import (
    TeamsMeetingParticipant,
    TeamsMeetingInfo,
    MeetingParticipantInfo,
)

# Import our components
from ..asr.whisper_asr import WhisperASR
from ..translation.nllb_translator import NLLBTranslator
from ..tts.piper_tts import PiperTTS

# Set up logging
logger = logging.getLogger(__name__)

class InterpreterBot:
    """
    Teams meeting interpreter bot that provides real-time translation.
    """
    
    def __init__(
        self,
        config_path: str,
        asr: WhisperASR,
        translator: NLLBTranslator,
        tts: PiperTTS
    ):
        """
        Initialize the interpreter bot.
        
        Args:
            config_path: Path to the bot configuration file
            asr: Speech recognition instance
            translator: Translation instance
            tts: Text-to-speech instance
        """
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Store components
        self.asr = asr
        self.translator = translator
        self.tts = tts
        
        # Set up Bot Framework components
        self.adapter_settings = BotFrameworkAdapterSettings(
            app_id=self.config.get("app_id"),
            app_password=self.config.get("app_password")
        )
        self.adapter = BotFrameworkAdapter(self.adapter_settings)
        
        # Error handler
        self.adapter.on_turn_error = self._on_error
        
        # State management
        self.memory = MemoryStorage()
        self.conversation_state = ConversationState(self.memory)
        self.user_state = UserState(self.memory)
        
        # Track active meetings
        self.active_meetings = {}  # meeting_id -> meeting_info
        self.user_languages = {}   # user_id -> language_code
        
        logger.info("Interpreter bot initialized")
    
    async def _on_error(self, context: TurnContext, error: Exception):
        """Handle errors during bot execution"""
        logger.error(f"Bot error: {str(error)}")
        
        # Send a message to the user
        await context.send_activity("Sorry, something went wrong. Please try again.")
        
        # Save state changes
        await self.conversation_state.save_changes(context)
        await self.user_state.save_changes(context)
    
    async def on_turn(self, turn_context: TurnContext):
        """
        Process an incoming activity.
        
        Args:
            turn_context: The current turn context
        """
        if turn_context.activity.type == ActivityTypes.message:
            await self._handle_message(turn_context)
        elif turn_context.activity.type == ActivityTypes.conversation_update:
            await self._handle_conversation_update(turn_context)
        elif turn_context.activity.type == ActivityTypes.invoke:
            await self._handle_invoke(turn_context)
        
        # Save state changes
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)
    
    async def _handle_message(self, turn_context: TurnContext):
        """
        Handle incoming messages from users.
        
        Args:
            turn_context: The current turn context
        """
        # Get the text of the message
        text = turn_context.activity.text.strip()
        sender_id = turn_context.activity.from_property.id
        
        # Check if it's a command
        if text.startswith('/'):
            await self._handle_command(turn_context, text)
            return
        
        # Handle normal message (for testing outside of meetings)
        # In a real meeting scenario, we'd be processing audio streams
        
        # Get the user's language preference
        user_language = self.user_languages.get(sender_id, "en-US")
        
        # Translate to other supported languages
        translations = {}
        for target_lang in self.config["languages"]["supported"]:
            if target_lang != user_language:
                translated_text = self.translator.translate(text, user_language, target_lang)
                translations[target_lang] = translated_text
        
        # Respond with translations
        response = f"Your message: {text}\n\nTranslations:\n"
        for lang, translated in translations.items():
            response += f"\n{lang}: {translated}"
        
        await turn_context.send_activity(response)
    
    async def _handle_command(self, turn_context: TurnContext, command: str):
        """
        Handle bot commands from users.
        
        Args:
            turn_context: The current turn context
            command: The command text including the / prefix
        """
        sender_id = turn_context.activity.from_property.id
        
        # Extract command and arguments
        parts = command[1:].split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == "help":
            help_text = (
                "Available commands:\n"
                "/help - Show this help message\n"
                "/language [code] - Set your language (en-US, ru-RU, es-CO)\n"
                "/status - Check bot status\n"
            )
            await turn_context.send_activity(help_text)
        
        elif cmd == "language":
            if not args:
                current_lang = self.user_languages.get(sender_id, "en-US")
                await turn_context.send_activity(
                    f"Your current language is set to: {current_lang}\n"
                    "To change it, use: /language [code]\n"
                    "Supported codes: en-US, ru-RU, es-CO"
                )
            else:
                lang_code = args.strip()
                if lang_code in self.config["languages"]["supported"]:
                    self.user_languages[sender_id] = lang_code
                    await turn_context.send_activity(f"Your language has been set to: {lang_code}")
                else:
                    await turn_context.send_activity(
                        f"Unsupported language code: {lang_code}\n"
                        "Supported codes: en-US, ru-RU, es-CO"
                    )
        
        elif cmd == "status":
            status = (
                f"Bot status: Active\n"
                f"Active meetings: {len(self.active_meetings)}\n"
                f"Your language: {self.user_languages.get(sender_id, 'en-US')}\n"
            )
            await turn_context.send_activity(status)
        
        else:
            await turn_context.send_activity(f"Unknown command: {cmd}\nType /help for available commands.")
    
    async def _handle_conversation_update(self, turn_context: TurnContext):
        """
        Handle conversation update activities.
        
        Args:
            turn_context: The current turn context
        """
        # Handle when the bot is added to a conversation
        if turn_context.activity.members_added:
            for member in turn_context.activity.members_added:
                if member.id != turn_context.activity.recipient.id:
                    # Bot was added to a conversation
                    await turn_context.send_activity(
                        "Hello! I'm the Teams Interpreter Bot. I can help translate conversations "
                        "in meetings between English, Russian, and Spanish. Type /help for commands."
                    )
    
    async def _handle_invoke(self, turn_context: TurnContext):
        """
        Handle invoke activities including meeting events.
        
        Args:
            turn_context: The current turn context
        """
        # The actual implementation would handle various meeting events
        # like meeting start, end, and participant join/leave
        
        # For this example, we'll just acknowledge the invoke
        invoke_name = turn_context.activity.name
        logger.info(f"Received invoke: {invoke_name}")
        
        # Acknowledge the invoke to prevent timeout errors
        await turn_context.send_activity(Activity(type=ActivityTypes.invoke_response, value={"status": 200}))
    
    async def join_meeting(self, meeting_id: str, organizer_id: str):
        """
        Join a Teams meeting.
        
        Args:
            meeting_id: The Teams meeting ID
            organizer_id: The ID of the meeting organizer
        
        Returns:
            True if successfully joined, False otherwise
        """
        # In a real implementation, this would call the Teams API to join the meeting
        # For this example, we'll simulate joining
        
        logger.info(f"Joining meeting: {meeting_id}")
        
        # Store meeting info
        self.active_meetings[meeting_id] = {
            "id": meeting_id,
            "organizer_id": organizer_id,
            "participants": {},
            "start_time": None,  # Would be set to current time in real implementation
            "language_mappings": {}  # user_id -> language_code
        }
        
        logger.info(f"Successfully joined meeting: {meeting_id}")
        return True
    
    async def leave_meeting(self, meeting_id: str):
        """
        Leave a Teams meeting.
        
        Args:
            meeting_id: The Teams meeting ID
        
        Returns:
            True if successfully left, False otherwise
        """
        if meeting_id in self.active_meetings:
            # In a real implementation, this would call the Teams API to leave the meeting
            # For this example, we'll simulate leaving
            
            logger.info(f"Leaving meeting: {meeting_id}")
            del self.active_meetings[meeting_id]
            logger.info(f"Successfully left meeting: {meeting_id}")
            return True
        else:
            logger.warning(f"Attempted to leave unknown meeting: {meeting_id}")
            return False
    
    async def transcribe_audio(self, audio_data, user_id: str, meeting_id: str):
        """
        Transcribe audio from a meeting participant.
        
        Args:
            audio_data: The audio data to transcribe
            user_id: The ID of the user speaking
            meeting_id: The ID of the meeting
            
        Returns:
            The transcribed text
        """
        # Get the user's language
        meeting_info = self.active_meetings.get(meeting_id)
        if not meeting_info:
            logger.warning(f"Transcription requested for unknown meeting: {meeting_id}")
            return None
        
        user_language = meeting_info["language_mappings"].get(
            user_id, self.user_languages.get(user_id, "en-US")
        )
        
        # Transcribe the audio
        transcribed_text = self.asr.transcribe(audio_data, user_language)
        
        logger.info(f"Transcribed text from user {user_id}: {transcribed_text}")
        return transcribed_text
    
    async def translate_and_speak(self, text: str, source_lang: str, target_lang: str):
        """
        Translate text and synthesize speech.
        
        Args:
            text: The text to translate
            source_lang: The source language code
            target_lang: The target language code
            
        Returns:
            Audio data of the synthesized speech
        """
        # Translate the text
        translated_text = self.translator.translate(text, source_lang, target_lang)
        
        # Convert to speech
        audio_data = self.tts.synthesize(translated_text, target_lang)
        
        return audio_data
    
    async def get_participant_language(self, participant_id: str, meeting_id: str):
        """
        Get a participant's language preference.
        
        Args:
            participant_id: The participant's ID
            meeting_id: The meeting ID
            
        Returns:
            The language code for the participant
        """
        meeting_info = self.active_meetings.get(meeting_id)
        if meeting_info and participant_id in meeting_info["language_mappings"]:
            return meeting_info["language_mappings"][participant_id]
        
        return self.user_languages.get(participant_id, self.config["languages"]["default"])
    
    async def set_participant_language(self, participant_id: str, meeting_id: str, language_code: str):
        """
        Set a participant's language preference for a specific meeting.
        
        Args:
            participant_id: The participant's ID
            meeting_id: The meeting ID
            language_code: The language code to set
            
        Returns:
            True if successful, False otherwise
        """
        if language_code not in self.config["languages"]["supported"]:
            logger.warning(f"Attempted to set unsupported language: {language_code}")
            return False
        
        meeting_info = self.active_meetings.get(meeting_id)
        if not meeting_info:
            logger.warning(f"Attempted to set language for unknown meeting: {meeting_id}")
            return False
        
        meeting_info["language_mappings"][participant_id] = language_code
        logger.info(f"Set language for participant {participant_id} to {language_code} in meeting {meeting_id}")
        return True
    
    # Additional methods for meeting functionality would be implemented here 