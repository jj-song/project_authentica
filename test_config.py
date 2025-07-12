#!/usr/bin/env python3
"""
Test script for the new configuration system.
"""

import os
import sys
import logging

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.config import init_configuration, get_reddit_instance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ConfigTest")

def test_configuration():
    """Test the configuration system."""
    try:
        # Initialize configuration
        logger.info("Initializing configuration...")
        config = init_configuration()
        
        # Print the configuration
        logger.info("Configuration loaded successfully!")
        print("\nConfiguration:")
        for section, values in config.items():
            print(f"\n[{section}]")
            for key, value in values.items():
                # Mask API key for security
                if key == "api_key":
                    value = f"{value[:5]}...{value[-5:]}" if value else "None"
                print(f"{key}: {value}")
        
        # Test Reddit authentication if a bot username is specified
        bot_username = config["runtime"]["bot_username"]
        if bot_username:
            logger.info(f"\nTesting Reddit authentication as {bot_username}...")
            try:
                reddit = get_reddit_instance(bot_username)
                logger.info(f"Successfully authenticated as {reddit.user.me()}")
            except Exception as e:
                logger.error(f"Reddit authentication failed: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Configuration test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_configuration()
    sys.exit(0 if success else 1) 