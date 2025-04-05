#!/usr/bin/env python3
"""
Test script for the simple server
"""

import requests
import time
import json

def test_server():
    """Test the simple server"""
    print("Testing simple server...")
    
    # Test the root endpoint
    try:
        response = requests.get("http://localhost:8080/")
        print(f"Root endpoint - Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            
            # Test the echo endpoint
            test_data = {"message": "Hello, Server!", "data": {"key": "value"}}
            echo_response = requests.post(
                "http://localhost:8080/api/echo", 
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\nEcho endpoint - Status Code: {echo_response.status_code}")
            if echo_response.status_code == 200:
                print(f"Response: {json.dumps(echo_response.json(), indent=2)}")
                return True
            else:
                print(f"Error: {echo_response.text}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}")
    
    return False

if __name__ == "__main__":
    # Try a few times with a delay
    for i in range(3):
        if test_server():
            print("\nTest completed successfully!")
            break
        else:
            print(f"\nRetrying in 2 seconds... (Attempt {i+1}/3)")
            time.sleep(2)
    else:
        print("\nFailed to connect to the simple server.") 