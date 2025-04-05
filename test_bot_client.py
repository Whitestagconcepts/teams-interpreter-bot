#!/usr/bin/env python3
"""
Test client for the simple bot server
"""

import requests
import json
import time

def test_bot_server():
    """Test the bot server endpoints"""
    base_url = "http://localhost:3978"
    
    print("Testing bot server...")
    
    try:
        # Test health check endpoint
        print("\n1. Testing health check endpoint...")
        response = requests.get(f"{base_url}/")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"Translator Ready: {data.get('translator_ready', False)}")
        else:
            print(f"Error: {response.text}")
            return False
        
        # Test status endpoint
        print("\n2. Testing status endpoint...")
        response = requests.get(f"{base_url}/api/status")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(f"Error: {response.text}")
            return False
        
        # Test English to Spanish translation
        print("\n3. Testing English to Spanish translation...")
        data = {
            "text": "Hello, how are you today?",
            "language": "en-US",
            "target_language": "es-CO"
        }
        
        response = requests.post(
            f"{base_url}/api/messages", 
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Original: {result.get('original', '')}")
            print(f"Translated: {result.get('translated', '')}")
            print(f"Source Language: {result.get('source_language', '')}")
            print(f"Target Language: {result.get('target_language', '')}")
        else:
            print(f"Error: {response.text}")
            return False
        
        # Test Spanish to English translation
        print("\n4. Testing Spanish to English translation...")
        data = {
            "text": "Hola, ¿cómo estás hoy?",
            "language": "es-CO",
            "target_language": "en-US"
        }
        
        response = requests.post(
            f"{base_url}/api/messages", 
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Original: {result.get('original', '')}")
            print(f"Translated: {result.get('translated', '')}")
            print(f"Source Language: {result.get('source_language', '')}")
            print(f"Target Language: {result.get('target_language', '')}")
        else:
            print(f"Error: {response.text}")
            return False
        
        # Test Russian to English translation if available
        print("\n5. Testing Russian to English translation...")
        data = {
            "text": "Привет, как дела сегодня?",
            "language": "ru-RU",
            "target_language": "en-US"
        }
        
        response = requests.post(
            f"{base_url}/api/messages", 
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Original: {result.get('original', '')}")
            print(f"Translated: {result.get('translated', '')}")
            print(f"Source Language: {result.get('source_language', '')}")
            print(f"Target Language: {result.get('target_language', '')}")
        else:
            print(f"Error: {response.text}")
        
        print("\nTests completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error connecting to bot server: {e}")
        return False

if __name__ == "__main__":
    # Try a few times with a delay between attempts
    max_attempts = 3
    for i in range(max_attempts):
        print(f"\nAttempt {i+1}/{max_attempts}")
        if test_bot_server():
            break
        if i < max_attempts - 1:
            print(f"Retrying in 5 seconds...")
            time.sleep(5)
    else:
        print("\nFailed to connect to the bot server after multiple attempts.") 