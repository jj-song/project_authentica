#!/usr/bin/env python3
"""
Configuration module for Project Authentica.
Handles Reddit API authentication using PRAW.
"""

import os
import configparser
from typing import Optional

import praw
import prawcore.exceptions

# Function removed - now using praw.ini directly
# def get_config():
#     """
#     Load and return the configuration from config.json.
#     
#     Returns:
#         dict: A dictionary containing the configuration data.
#     """
#     config_path = os.path.join(os.path.dirname(__file__), 'config.json')
#     if not os.path.exists(config_path):
#         raise FileNotFoundError(f"config.json not found at {config_path}")
#     
#     import json
#     with open(config_path, 'r') as f:
#         return json.load(f)


def get_reddit_instance(bot_username):
    """
    Get a Reddit instance for the specified bot.
    
    Args:
        bot_username (str): The username of the bot to authenticate as.
        
    Returns:
        praw.Reddit: A Reddit instance authenticated as the specified bot.
        
    Raises:
        ValueError: If the bot credentials are not found or authentication fails.
    """
    try:
        # Use the provided site name from praw.ini
        reddit = praw.Reddit(bot_username)
        
        try:
            # Try to access user info to verify authentication
            _ = reddit.user.me()
            return reddit
        except prawcore.exceptions.Forbidden:
            raise ValueError(f"Account '{reddit.config.username}' appears to be banned or suspended from Reddit")
        except prawcore.exceptions.ResponseException as e:
            if e.response.status_code == 401:
                raise ValueError(f"Authentication failed for '{reddit.config.username}'. Check username and password.")
            else:
                raise ValueError(f"Error accessing Reddit API: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error initializing Reddit instance for '{bot_username}': {str(e)}")


if __name__ == "__main__":
    # Example usage (for testing purposes)
    import sys
    
    if len(sys.argv) > 1:
        test_username = sys.argv[1]
        try:
            reddit = get_reddit_instance(test_username)
            print(f"Successfully authenticated as: {reddit.user.me()}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python config.py <bot_username>") 