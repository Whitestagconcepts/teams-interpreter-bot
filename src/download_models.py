#!/usr/bin/env python3
"""
Download and prepare the required ML models for the Teams Interpreter Bot.
This script downloads:
- Whisper.cpp tiny model for ASR
- NLLB-200 small model for translation
- Piper voice models for TTS

Usage:
    python download_models.py
"""

import os
import json
import sys
import requests
import tarfile
import zipfile
import subprocess
from pathlib import Path
from tqdm import tqdm
import shutil
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("model_downloader")

# Constants
WHISPER_MODELS_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
WHISPER_MODEL_NAME = "ggml-tiny.en.bin"  # English-only tiny model, very small
NLLB_MODEL_NAME = "nllb-200-distilled-600M"  # Smaller NLLB model
NLLB_MODEL_URL = f"https://huggingface.co/facebook/{NLLB_MODEL_NAME}/resolve/main"
PIPER_VOICES_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

# Define base paths
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
ASR_MODELS_DIR = MODELS_DIR / "asr"
TRANSLATION_MODELS_DIR = MODELS_DIR / "translation"
TTS_MODELS_DIR = MODELS_DIR / "tts"
CONFIG_DIR = BASE_DIR / "config"

# Ensure directories exist
os.makedirs(ASR_MODELS_DIR, exist_ok=True)
os.makedirs(TRANSLATION_MODELS_DIR, exist_ok=True)
os.makedirs(TTS_MODELS_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# Download progress hook for tqdm
def download_with_progress(url, dest_path):
    """Download a file with a progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024  # 1 Kibibyte
    
    logger.info(f"Downloading {url} to {dest_path}")
    
    with open(dest_path, 'wb') as f, tqdm(
            desc=dest_path.name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
        for data in response.iter_content(block_size):
            size = f.write(data)
            bar.update(size)
    
    logger.info(f"Download complete: {dest_path}")
    return dest_path

def extract_archive(archive_path, extract_dir):
    """Extract a zip or tar archive"""
    logger.info(f"Extracting {archive_path} to {extract_dir}")
    
    if archive_path.suffix == '.zip':
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    elif archive_path.suffix in ['.tar', '.gz', '.tgz']:
        with tarfile.open(archive_path, 'r:*') as tar_ref:
            tar_ref.extractall(extract_dir)
    
    logger.info(f"Extraction complete: {extract_dir}")

def download_whisper_model():
    """Download the Whisper.cpp model"""
    logger.info("=== Downloading Whisper model ===")
    
    model_url = f"{WHISPER_MODELS_URL}/{WHISPER_MODEL_NAME}"
    model_path = ASR_MODELS_DIR / WHISPER_MODEL_NAME
    
    if model_path.exists():
        logger.info(f"Whisper model already exists at {model_path}")
        return
    
    download_with_progress(model_url, model_path)
    logger.info("Whisper model download complete")

def download_nllb_model():
    """Download the NLLB translation model"""
    logger.info("=== Downloading NLLB translation model ===")
    
    # NLLB requires several files, we'll download the config and tokenizer first
    files_to_download = [
        "config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "sentencepiece.bpe.model",
        "special_tokens_map.json",
        "pytorch_model.bin",  # This is the actual model weights, will be large
    ]
    
    model_dir = TRANSLATION_MODELS_DIR / NLLB_MODEL_NAME
    os.makedirs(model_dir, exist_ok=True)
    
    for file in files_to_download:
        file_path = model_dir / file
        
        if file_path.exists():
            logger.info(f"NLLB file already exists: {file}")
            continue
            
        file_url = f"{NLLB_MODEL_URL}/{file}"
        download_with_progress(file_url, file_path)
    
    logger.info("NLLB model download complete")

def download_piper_voices():
    """Download Piper TTS voices for supported languages"""
    logger.info("=== Downloading Piper voices ===")
    
    # Define the voices we want
    voices = [
        "en_US-lessac-medium",  # US English voice
        "ru_RU-irina-medium",   # Russian voice
        "es_LA-google-medium",  # Latin American Spanish voice (closest to Colombian)
    ]
    
    for voice in voices:
        voice_dir = TTS_MODELS_DIR / voice
        voice_file = f"{voice}.onnx"
        config_file = f"{voice}.json"
        
        # Create voice directory
        os.makedirs(voice_dir, exist_ok=True)
        
        # Check if files already exist
        voice_path = voice_dir / voice_file
        config_path = voice_dir / config_file
        
        if voice_path.exists() and config_path.exists():
            logger.info(f"Piper voice already exists: {voice}")
            continue
            
        # Download voice model
        voice_url = f"{PIPER_VOICES_URL}/{voice_file}"
        config_url = f"{PIPER_VOICES_URL}/{config_file}"
        
        download_with_progress(voice_url, voice_path)
        download_with_progress(config_url, config_path)
    
    logger.info("Piper voices download complete")

def create_model_config():
    """Create a model configuration file with paths to all models"""
    logger.info("=== Creating model configuration ===")
    
    config = {
        "asr": {
            "engine": "whisper.cpp",
            "model_path": str(ASR_MODELS_DIR / WHISPER_MODEL_NAME),
            "languages": {
                "en-US": "english",
                "ru-RU": "russian",
                "es-CO": "spanish"
            }
        },
        "translation": {
            "engine": "nllb",
            "model_path": str(TRANSLATION_MODELS_DIR / NLLB_MODEL_NAME),
            "language_codes": {
                "en-US": "eng_Latn",
                "ru-RU": "rus_Cyrl",
                "es-CO": "spa_Latn"
            }
        },
        "tts": {
            "engine": "piper",
            "voices": {
                "en-US": str(TTS_MODELS_DIR / "en_US-lessac-medium" / "en_US-lessac-medium.onnx"),
                "ru-RU": str(TTS_MODELS_DIR / "ru_RU-irina-medium" / "ru_RU-irina-medium.onnx"),
                "es-CO": str(TTS_MODELS_DIR / "es_LA-google-medium" / "es_LA-google-medium.onnx")
            }
        }
    }
    
    config_path = CONFIG_DIR / "model_config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Model configuration saved to {config_path}")

def main():
    """Run the full model download process"""
    logger.info("Starting model download process")
    
    try:
        download_whisper_model()
        download_nllb_model()
        download_piper_voices()
        create_model_config()
        
        logger.info("All models downloaded successfully!")
        logger.info(f"Models stored in: {MODELS_DIR}")
    except Exception as e:
        logger.error(f"Error during model download: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 