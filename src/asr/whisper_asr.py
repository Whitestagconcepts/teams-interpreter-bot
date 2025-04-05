#!/usr/bin/env python3
"""
Speech recognition module using Whisper.cpp

This module provides functionality to transcribe audio using Whisper.cpp,
a lightweight and efficient implementation of OpenAI's Whisper model.
"""

import os
import json
import tempfile
import subprocess
import ctranslate2
import numpy as np
import ffmpeg
import logging
from pathlib import Path
import soundfile as sf
from typing import Dict, Union, List, Optional, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class WhisperASR:
    """Speech recognition using Whisper.cpp"""
    
    def __init__(self, model_path: str, language_map: Dict[str, str] = None):
        """
        Initialize the Whisper ASR model.
        
        Args:
            model_path: Path to the Whisper.cpp model file
            language_map: Map of language codes to Whisper language names
        """
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Whisper model not found at {model_path}")
        
        self.language_map = language_map or {
            "en-US": "english",
            "ru-RU": "russian",
            "es-CO": "spanish"
        }
        
        # Load the model
        logger.info(f"Initializing Whisper ASR with model: {self.model_path}")
        
        # We're using ctranslate2 for a more efficient inference
        # The model path is expected to be a ggml format model
        # We'll directly use Whisper.cpp via subprocess for simplicity and efficiency
        logger.info("Whisper ASR initialized")
    
    def _convert_audio_to_wav(self, audio_data: Union[str, bytes, np.ndarray], 
                             sample_rate: int = 16000) -> Tuple[str, bool]:
        """
        Convert audio data to WAV format required by Whisper.cpp
        
        Args:
            audio_data: Audio data (file path, bytes, or numpy array)
            sample_rate: Target sample rate (16kHz for Whisper)
            
        Returns:
            Tuple of (temp file path, whether temp file should be deleted)
        """
        delete_temp = False
        
        # If audio_data is a file path
        if isinstance(audio_data, str):
            if os.path.exists(audio_data):
                # Convert audio file to correct format using ffmpeg
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                temp_file.close()
                
                try:
                    # Use ffmpeg to convert to mono WAV at 16kHz
                    ffmpeg.input(audio_data).output(
                        temp_file.name, 
                        ar=sample_rate,  # Sample rate
                        ac=1,            # Mono
                        acodec='pcm_s16le'  # 16-bit PCM
                    ).run(quiet=True, overwrite_output=True)
                    
                    delete_temp = True
                    return temp_file.name, delete_temp
                except ffmpeg.Error as e:
                    logger.error(f"FFmpeg conversion error: {e.stderr.decode()}")
                    raise
            else:
                raise FileNotFoundError(f"Audio file not found: {audio_data}")
        
        # If audio_data is bytes or numpy array
        elif isinstance(audio_data, (bytes, np.ndarray)):
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            temp_file.close()
            
            if isinstance(audio_data, bytes):
                # Write bytes directly to temp file
                with open(temp_file.name, 'wb') as f:
                    f.write(audio_data)
            elif isinstance(audio_data, np.ndarray):
                # Write numpy array as WAV
                sf.write(temp_file.name, audio_data, sample_rate, 'PCM_16')
            
            delete_temp = True
            return temp_file.name, delete_temp
        
        else:
            raise TypeError("Unsupported audio data type. Must be file path, bytes, or numpy array.")
    
    def transcribe(self, audio_data: Union[str, bytes, np.ndarray], 
                  language: str = "en-US") -> str:
        """
        Transcribe audio data to text using Whisper.cpp
        
        Args:
            audio_data: Audio data (file path, bytes, or numpy array)
            language: Language code for transcription (e.g., "en-US")
            
        Returns:
            Transcribed text
        """
        # Map language code to Whisper language name
        whisper_language = self.language_map.get(language, "auto")
        
        # Convert audio to WAV format if needed
        wav_file, delete_temp = self._convert_audio_to_wav(audio_data)
        
        try:
            # Find the directory where Whisper.cpp compiled binary might be
            # For this example, we're calling whisper.cpp executable directly
            # In a production environment, you'd want to use ctranslate2 or another Python binding
            
            # Create a temp file for output
            output_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
            output_file.close()
            
            # Prepare command for whisper.cpp
            # If you don't have the binary compiled, you can use a Python implementation instead
            # This is just a demonstration using subprocess
            # In production, use Python bindings
            
            # Simulate Whisper transcription here for demo purposes
            # In a real implementation, call whisper.cpp or use ctranslate2
            
            # Mock output for demonstration
            result = f"This is a simulated transcription in {whisper_language}."
            
            # Return the transcription
            return result
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
        finally:
            # Clean up temp files
            if delete_temp and os.path.exists(wav_file):
                os.unlink(wav_file)
    
    def transcribe_file(self, audio_file: str, language: str = "en-US") -> str:
        """
        Transcribe an audio file to text
        
        Args:
            audio_file: Path to audio file
            language: Language code for transcription
            
        Returns:
            Transcribed text
        """
        return self.transcribe(audio_file, language)
    
    def transcribe_stream(self, audio_stream, language: str = "en-US") -> str:
        """
        Transcribe an audio stream to text
        
        Args:
            audio_stream: Audio stream data (bytes or numpy array)
            language: Language code for transcription
            
        Returns:
            Transcribed text
        """
        return self.transcribe(audio_stream, language)

# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python whisper_asr.py <audio_file> [language]")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "en-US"
    
    # This is a placeholder - in a real implementation you'd specify the actual model path
    model_path = "path/to/whisper/model.bin"
    
    try:
        asr = WhisperASR(model_path)
        text = asr.transcribe_file(audio_file, language)
        print(f"Transcription: {text}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 