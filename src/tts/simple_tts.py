#!/usr/bin/env python3
"""
Simple TTS Module using pyttsx3 for Windows

This module provides basic text-to-speech functionality using the
Windows SAPI voices through pyttsx3 library.
"""

import os
import logging
import tempfile
from typing import Dict, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class SimpleTTS:
    """Text-to-speech service using pyttsx3"""
    
    def __init__(self):
        """Initialize the TTS engine"""
        self.engine = None
        self.voice_map = {}
        self.ready = False
        
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.ready = True
            
            # Get available voices
            voices = self.engine.getProperty('voices')
            logger.info(f"Found {len(voices)} system voices")
            
            # Set default speech rate and volume
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
            
            # Map language codes to voice IDs if possible
            self.voice_map = {}
            default_voice = voices[0].id if voices else None
            
            # Log available voices
            for i, voice in enumerate(voices):
                logger.info(f"Voice {i}: ID={voice.id}, Name={voice.name}")
                # Try to detect language from voice name or ID
                if default_voice is None:
                    default_voice = voice.id
                
                voice_id = voice.id.lower() if voice.id else ""
                voice_name = voice.name.lower() if voice.name else ""
                
                # Try to detect English voice
                if "english" in voice_name or "en-us" in voice_name or "en_us" in voice_name:
                    self.voice_map["en-US"] = voice.id
                    logger.info(f"Mapped en-US to voice {voice.name}")
                    
                # Try to detect Spanish voice
                elif "spanish" in voice_name or "español" in voice_name or "es-" in voice_name:
                    self.voice_map["es-CO"] = voice.id
                    logger.info(f"Mapped es-CO to voice {voice.name}")
                    
                # Try to detect Russian voice
                elif "russian" in voice_name or "русский" in voice_name or "ru-" in voice_name:
                    self.voice_map["ru-RU"] = voice.id
                    logger.info(f"Mapped ru-RU to voice {voice.name}")
            
            # Use default voice for any unmapped languages
            for lang in ["en-US", "es-CO", "ru-RU"]:
                if lang not in self.voice_map:
                    self.voice_map[lang] = default_voice
                    logger.info(f"Using default voice for {lang}")
                    
            logger.info("TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            logger.warning("TTS functionality will be unavailable")
    
    def text_to_speech(self, text: str, language: str) -> str:
        """
        Convert text to speech and return the path to the audio file
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., "en-US")
            
        Returns:
            Path to the audio file, or empty string if failed
        """
        if not self.ready or not self.engine:
            logger.warning("TTS engine not ready")
            return ""
            
        if not text:
            logger.warning("Empty text provided for TTS")
            return ""
            
        try:
            # Create a temporary file for the output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                output_path = temp_file.name
                
            # Set the voice based on language
            if language in self.voice_map:
                voice_id = self.voice_map[language]
                self.engine.setProperty('voice', voice_id)
                logger.info(f"Using voice {voice_id} for {language}")
            else:
                logger.warning(f"No voice mapping for {language}, using default")
                
            # Convert text to speech and save to file
            logger.info(f"Converting to speech: '{text[:50]}...' in {language}")
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            
            # Check if file was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Speech saved to {output_path}")
                return output_path
            else:
                logger.warning(f"Failed to create speech file or file is empty")
                return ""
                
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return ""
    
    def speak(self, text: str, language: str) -> bool:
        """
        Speak the text directly without saving to file
        
        Args:
            text: Text to speak
            language: Language code (e.g., "en-US")
            
        Returns:
            True if successful, False otherwise
        """
        if not self.ready or not self.engine:
            logger.warning("TTS engine not ready")
            return False
            
        if not text:
            logger.warning("Empty text provided for TTS")
            return False
            
        try:
            # Set the voice based on language
            if language in self.voice_map:
                voice_id = self.voice_map[language]
                self.engine.setProperty('voice', voice_id)
                logger.info(f"Using voice {voice_id} for {language}")
            else:
                logger.warning(f"No voice mapping for {language}, using default")
                
            # Speak the text
            logger.info(f"Speaking: '{text[:50]}...' in {language}")
            self.engine.say(text)
            self.engine.runAndWait()
            return True
            
        except Exception as e:
            logger.error(f"Error speaking text: {e}")
            return False
            
# For testing
if __name__ == "__main__":
    import sys
    
    # Create TTS engine
    tts = SimpleTTS()
    
    if not tts.ready:
        print("TTS engine not ready")
        sys.exit(1)
        
    if len(sys.argv) < 3:
        print("Usage: python simple_tts.py <text> <language> [output_file]")
        sys.exit(1)
        
    text = sys.argv[1]
    language = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    if output_file:
        path = tts.text_to_speech(text, language)
        if path:
            print(f"Speech saved to {path}")
            if path != output_file:
                # Copy to requested output file
                import shutil
                shutil.copy(path, output_file)
                print(f"Copied to {output_file}")
        else:
            print("Failed to convert text to speech")
            sys.exit(1)
    else:
        success = tts.speak(text, language)
        if success:
            print("Text spoken successfully")
        else:
            print("Failed to speak text")
            sys.exit(1) 