#!/usr/bin/env python3
"""
Main entry point for the Teams Interpreter Bot

This script initializes the bot components and starts the server.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Import the server
from src.server.app import app, logger

def main():
    """
    Main function to start the bot server
    """
    try:
        logger.info("Starting Teams Interpreter Bot")
        
        # Get server configuration from environment variables
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 3978))
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
        
        # Log server information
        logger.info(f"Starting server on {host}:{port}")
        
        # Run the Flask application
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 