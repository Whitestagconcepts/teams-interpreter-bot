#!/usr/bin/env python3
"""
Text-to-speech module using Windows TTS (pyttsx3)

This module provides functionality to synthesize speech from text
using the pyttsx3 library which works with Windows SAPI voices.
"""

import os
import json
import tempfile
import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, Union, Tuple

import numpy as np
import soundfile as sf
import pyttsx3

# Set up logging
logger = logging.getLogger(__name__)

class PiperTTS:
    """Text-to-speech service using pyttsx3"""
    
    def __init__(self, voice_map: Dict[str, str]):
        """
        Initialize the TTS system.
        
        Args:
            voice_map: Map of language codes to voice paths (not used with pyttsx3 but kept for compatibility)
        """
        self.voice_map = voice_map
        logger.info(f"Initialized TTS with {len(self.voice_map)} voice configurations")
        
        # Initialize pyttsx3 engine
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
            
            # Get available voices
            voices = self.engine.getProperty('voices')
            
            logger.info(f"Found {len(voices)} system voices")
            for i, voice in enumerate(voices):
                logger.info(f"Voice {i}: ID={voice.id}, Name={voice.name}, Languages={voice.languages}")
            
            self.available_voices = {voice.id: voice for voice in voices}
            
            # Map language codes to voice IDs
            self.voice_id_map = {
                'en-US': None,  # Will be set to default English voice
                'es-CO': None,  # Will find Spanish voice if available
                'ru-RU': None,  # Will find Russian voice if available
            }
            
            # Try to find appropriate voices
            for voice in voices:
                voice_name = voice.name.lower() if voice.name else ""
                voice_id = voice.id.lower() if voice.id else ""
                voice_langs = [lang.lower() if lang else "" for lang in voice.languages]
                
                # Check for English voices
                if any(lang in voice_name or lang in voice_id or lang in str(voice_langs) 
                       for lang in ["english", "en-us", "en_us"]):
                    self.voice_id_map['en-US'] = voice.id
                    logger.info(f"Found English voice: {voice.name}")
                
                # Check for Spanish voices
                elif any(lang in voice_name or lang in voice_id or lang in str(voice_langs)
                         for lang in ["spanish", "es-", "español", "spa"]):
                    self.voice_id_map['es-CO'] = voice.id
                    logger.info(f"Found Spanish voice: {voice.name}")
                
                # Check for Russian voices
                elif any(lang in voice_name or lang in voice_id or lang in str(voice_langs)
                         for lang in ["russian", "ru-", "русский", "rus"]):
                    self.voice_id_map['ru-RU'] = voice.id
                    logger.info(f"Found Russian voice: {voice.name}")
            
            # Set default voice if specific language not found
            default_voice = voices[0].id if voices else None
            
            if not self.voice_id_map['en-US'] and default_voice:
                self.voice_id_map['en-US'] = default_voice
                logger.warning(f"No English voice found, using default: {default_voice}")
                
            if not self.voice_id_map['es-CO'] and default_voice:
                self.voice_id_map['es-CO'] = default_voice
                logger.warning(f"No Spanish voice found, using default: {default_voice}")
                
            if not self.voice_id_map['ru-RU'] and default_voice:
                self.voice_id_map['ru-RU'] = default_voice
                logger.warning(f"No Russian voice found, using default: {default_voice}")
            
            logger.info(f"Voice mappings: {self.voice_id_map}")
            
        except Exception as e:
            logger.error(f"Error initializing TTS engine: {e}")
            self.engine = None
    
    def _get_voice_id(self, language: str) -> str:
        """
        Get the voice ID for a language.
        
        Args:
            language: Language code (e.g., "en-US")
            
        Returns:
            Voice ID to use
        """
        if language in self.voice_id_map and self.voice_id_map[language]:
            return self.voice_id_map[language]
        
        # Try to find a fallback based on the language prefix
        lang_prefix = language.split('-')[0]
        for lang, voice_id in self.voice_id_map.items():
            if lang.startswith(lang_prefix) and voice_id:
                logger.info(f"Using fallback voice for {language}: {lang}")
                return voice_id
        
        # No fallback found, use any available voice
        if self.voice_id_map and any(self.voice_id_map.values()):
            for voice_id in self.voice_id_map.values():
                if voice_id:
                    logger.warning(f"Using default voice for {language}")
                    return voice_id
        
        # If still no voice found, return None and it will use the system default
        return None
    
    def synthesize(self, text: str, language: str) -> np.ndarray:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            language: Language code (e.g., "en-US")
            
        Returns:
            Audio data as numpy array
        """
        if not self.engine:
            logger.error("TTS engine not initialized")
            return np.zeros(8000, dtype=np.float32)  # Return silence
        
        try:
            # Create a temp file for the output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                output_path = temp_file.name
            
            # Set the voice
            voice_id = self._get_voice_id(language)
            if voice_id:
                logger.info(f"Using voice {voice_id} for language {language}")
                self.engine.setProperty('voice', voice_id)
            else:
                logger.warning(f"No voice found for {language}, using system default")
            
            # Save to file instead of speaking
            logger.info(f"Synthesizing text to {output_path}: {text[:50]}...")
            self.engine.save_to_file(text, output_path)
            self.engine.runAndWait()
            
            # Verify the output file exists and has content
            if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
                logger.warning(f"Output file is missing or too small: {output_path}")
                return np.zeros(16000, dtype=np.float32)  # Return silence
            
            # Read the output file
            audio_data, sample_rate = sf.read(output_path)
            logger.info(f"Read audio file with {len(audio_data)} samples at {sample_rate}Hz")
            
            # Clean up
            os.unlink(output_path)
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1 and audio_data.shape[1] > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            logger.info(f"Synthesized audio for '{text[:50]}...' in {language}")
            return audio_data
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return np.zeros(16000, dtype=np.float32)  # Return 1 second of silence
    
    def synthesize_to_file(self, text: str, language: str, output_path: str) -> bool:
        """
        Synthesize speech and save to a file.
        
        Args:
            text: Text to synthesize
            language: Language code (e.g., "en-US")
            output_path: Path to save the audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            audio_data = self.synthesize(text, language)
            sf.write(output_path, audio_data, 16000)  # 16kHz sample rate
            return True
        except Exception as e:
            logger.error(f"Error saving synthesized speech: {e}")
            return False

# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python pyttsx_tts.py <text> <language> [output_file]")
        sys.exit(1)
    
    text = sys.argv[1]
    language = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Use dummy voice map since we're using pyttsx3
    voice_map = {
        "en-US": "dummy_path",
        "ru-RU": "dummy_path",
        "es-CO": "dummy_path"
    }
    
    try:
        tts = PiperTTS(voice_map)
        
        if output_file:
            success = tts.synthesize_to_file(text, language, output_file)
            if success:
                print(f"Audio saved to {output_file}")
            else:
                print("Failed to save audio file")
                sys.exit(1)
        else:
            audio = tts.synthesize(text, language)
            print(f"Generated audio with {len(audio)} samples")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 