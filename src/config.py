#!/usr/bin/env python3
"""
Configuration module for Project Authentica.
Handles Reddit API authentication using PRAW.
"""

import os
import configparser
from typing import Optional

import praw


def get_reddit_instance(bot_username: str) -> praw.Reddit:
    """
    Initialize and return a PRAW Reddit instance for the specified bot username.
    
    This function reads API credentials from the praw.ini file in the project's
    root directory. The praw.ini file should be structured with separate sections
    for each bot, where the section name is the bot's username.
    
    Example praw.ini structure:
    ```
    [bot_username1]
    client_id=your_client_id_here
    client_secret=your_client_secret_here
    user_agent=python:project_authentica:v1.0 (by /u/your_username)
    username=bot_username1
    password=bot_password_here
    
    [bot_username2]
    client_id=another_client_id
    client_secret=another_client_secret
    user_agent=python:project_authentica:v1.0 (by /u/your_username)
    username=bot_username2
    password=another_password
    ```
    
    Each bot section must include:
    - client_id: The client ID from your Reddit app
    - client_secret: The client secret from your Reddit app
    - user_agent: A unique identifier following Reddit's API guidelines
    - username: The Reddit username (should match the section name)
    - password: The Reddit account password
    
    Args:
        bot_username (str): The username of the bot to authenticate as.
                           This must match a section name in praw.ini.
    
    Returns:
        praw.Reddit: An authenticated Reddit instance for the specified bot.
    
    Raises:
        ValueError: If the specified bot_username is not found in praw.ini.
        FileNotFoundError: If the praw.ini file doesn't exist.
    """
    try:
        # Check if the specified bot exists in the configuration
        reddit = praw.Reddit(bot_username)
        
        # Verify that we can access the configuration
        _ = reddit.user.me()
        
        return reddit
    except configparser.NoSectionError:
        raise ValueError(f"Bot username '{bot_username}' not found in praw.ini. "
                         f"Please add a [{bot_username}] section with the required credentials.")
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