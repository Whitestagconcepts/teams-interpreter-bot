#!/usr/bin/env python3
"""
Simple API test for the translation server.

This script tests the translation API endpoint by sending
sample messages and displaying the responses.
"""

import requests
import json
import sys

# Server URL
SERVER_URL = "http://localhost:5000"
API_ENDPOINT = f"{SERVER_URL}/api/messages"

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get(SERVER_URL)
        if response.status_code == 200:
            print(f"✓ Server is online: {response.json()}")
            return True
        else:
            print(f"✗ Server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Could not connect to server: {e}")
        return False

def test_translation(text, source_lang, target_lang=None):
    """Test the translation API"""
    payload = {
        "text": text,
        "language": source_lang
    }
    
    if target_lang:
        payload["target_language"] = target_lang
    
    print(f"\nSending: {text}")
    print(f"Source language: {source_lang}")
    if target_lang:
        print(f"Target language: {target_lang}")
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("\nResponse:")
            print(f"  Original [{result.get('source_language')}]: {result.get('original')}")
            print(f"  Translated [{result.get('target_language')}]: {result.get('translated')}")
            if "error" in result:
                print(f"  Error: {result.get('error')}")
            return True
        else:
            print(f"\n✗ Error: Status code {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"\n✗ Request failed: {e}")
        return False

def main():
    """Main function"""
    print("=== Translation API Test ===")
    
    # Check if server is running
    if not check_server_status():
        print("\nPlease make sure the server is running with:")
        print("  python translation_only_server.py")
        return
    
    # Test cases
    test_cases = [
        {"text": "Hello, how are you?", "source_lang": "en-US", "target_lang": "es-CO"},
        {"text": "Hola, ¿cómo estás?", "source_lang": "es-CO", "target_lang": "en-US"},
        {"text": "This is a test message", "source_lang": "en-US", "target_lang": "ru-RU"},
        {"text": "Привет, как дела?", "source_lang": "ru-RU", "target_lang": "en-US"}
    ]
    
    for test in test_cases:
        test_translation(
            test["text"],
            test["source_lang"],
            test["target_lang"]
        )
    
    print("\n=== Tests completed ===")

if __name__ == "__main__":
    main() 