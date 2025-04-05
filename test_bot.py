#!/usr/bin/env python3
"""
Test script for the Teams Interpreter Bot

This script tests the core functionality of the bot:
1. Translation between languages
2. Text-to-speech synthesis

Usage:
    python test_bot.py
"""

import os
import sys
import json
import requests
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Import directly from the bot modules
from src.translation.nllb_translator import NLLBTranslator
from src.tts.piper_tts import PiperTTS

def test_translation():
    """Test the translation module directly"""
    print("\n=== Testing Translation Module ===")
    
    # Initialize the translator
    try:
        translator = NLLBTranslator("")  # Model path is not relevant for MarianMT
        print("✓ Translator initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize translator: {e}")
        return
    
    # Test phrases
    test_phrases = [
        "Hello, how are you today?",
        "I need help with translation.",
        "The weather is nice."
    ]
    
    # Test language pairs
    language_pairs = [
        ("en-US", "es-CO"),
        ("en-US", "ru-RU"),
        ("es-CO", "en-US")
    ]
    
    # Perform translations
    for phrase in test_phrases:
        print(f"\nOriginal: {phrase}")
        
        for src_lang, tgt_lang in language_pairs:
            try:
                translated = translator.translate(phrase, src_lang, tgt_lang)
                print(f"✓ [{src_lang} → {tgt_lang}]: {translated}")
            except Exception as e:
                print(f"✗ [{src_lang} → {tgt_lang}] Error: {e}")
    
    print("\nTranslation test completed!")

def test_tts():
    """Test the text-to-speech module directly"""
    print("\n=== Testing Text-to-Speech Module ===")
    
    # Voice mapping - not actually used with pyttsx3 but kept for compatibility
    voice_map = {
        "en-US": "dummy",
        "ru-RU": "dummy",
        "es-CO": "dummy"
    }
    
    # Initialize TTS
    try:
        tts = PiperTTS(voice_map)
        print("✓ TTS system initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize TTS system: {e}")
        return
    
    # Test phrases for each language
    test_phrases = {
        "en-US": "Hello, this is a test of the speech synthesis system.",
        "es-CO": "Hola, esta es una prueba del sistema de síntesis de voz.",
        "ru-RU": "Привет, это тест системы синтеза речи."
    }
    
    # Create output directory
    output_dir = os.path.join(BASE_DIR, "test_output")
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ Output directory created at {output_dir}")
    
    # Generate audio for each language
    for lang, phrase in test_phrases.items():
        output_file = os.path.join(output_dir, f"test_{lang}.wav")
        print(f"\nGenerating speech for {lang}: '{phrase[:30]}...'")
        
        try:
            success = tts.synthesize_to_file(phrase, lang, output_file)
            if success and os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
                print(f"✓ Audio saved to {output_file} ({os.path.getsize(output_file)/1024:.1f} KB)")
            else:
                print(f"✗ Failed to generate valid audio file (file size: {os.path.getsize(output_file) if os.path.exists(output_file) else 0} bytes)")
        except Exception as e:
            print(f"✗ Error generating speech: {e}")
    
    print("\nText-to-speech test completed!")

def test_api():
    """Test the bot's API endpoint"""
    print("\n=== Testing Bot API ===")
    
    # Bot API endpoint
    bot_url = "http://localhost:3978/api/messages"
    
    # Test server connection first
    try:
        health_response = requests.get("http://localhost:3978/")
        print(f"✓ Server is running: {health_response.json() if health_response.status_code == 200 else 'No response'}")
    except Exception as e:
        print(f"✗ Server not available: {e}")
        print("  Make sure the server is running with: python simple_bot_server.py")
        return
    
    # Test messages with different languages
    test_messages = [
        {"text": "Hello, I need translation help.", "language": "en-US", "target_language": "es-CO"},
        {"text": "Hola, necesito ayuda con la traducción.", "language": "es-CO", "target_language": "en-US"}
    ]
    
    # Send each test message
    for msg in test_messages:
        try:
            print(f"\nSending: {msg['text']}")
            response = requests.post(
                bot_url,
                json=msg,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Response received:")
                print(f"  Original [{result.get('source_language', 'unknown')}]: {result.get('original', 'N/A')}")
                print(f"  Translated [{result.get('target_language', 'unknown')}]: {result.get('translated', 'N/A')}")
            else:
                print(f"✗ Error! Status code: {response.status_code}")
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"✗ Error sending request: {e}")
    
    print("\nAPI test completed!")

if __name__ == "__main__":
    print("=== Teams Interpreter Bot Test ===")
    print("Which test would you like to run?")
    print("1. Translation Module")
    print("2. Text-to-Speech Module")
    print("3. Bot API")
    print("4. All Tests")
    
    try:
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            test_translation()
        elif choice == "2":
            test_tts()
        elif choice == "3":
            test_api()
        elif choice == "4":
            test_translation()
            test_tts()
            test_api()
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}") 