#!/usr/bin/env python3
"""
Configuration module for Project Authentica.
Handles configuration loading from .env files and praw.ini.
"""

import os
import configparser
import logging
from typing import Dict, Any, Optional

import praw
import prawcore.exceptions
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Required environment variables for OpenAI API
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
]

# Optional environment variables with default values
DEFAULT_ENV_VARS = {
    "LLM_MODEL": "gpt-3.5-turbo",
    "LLM_TEMPERATURE": "0.7",
    "LLM_MAX_TOKENS": "250",
    "ENABLE_THREAD_ANALYSIS": "true",
    "ENABLE_HUMANIZATION": "true",
    "DRY_RUN": "false",
    "BOT_USERNAME": "my_first_bot",
    "SKIP_STICKIED_POSTS": "true",
    "SKIP_META_POSTS": "true",
    "MIN_POST_QUALITY_SCORE": "40",
}

def validate_environment() -> Dict[str, str]:
    """
    Validate that all required environment variables are set.
    
    Returns:
        Dict[str, str]: A dictionary containing all environment variables
        
    Raises:
        ValueError: If any required environment variables are missing
    """
    # Check for required variables
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        error_message = f"Missing required environment variables: {', '.join(missing_vars)}"
        logger.error(error_message)
        raise ValueError(error_message)
    
    # Set default values for optional variables if not present
    for var, default in DEFAULT_ENV_VARS.items():
        if not os.getenv(var):
            os.environ[var] = default
            logger.info(f"Setting default value for {var}: {default}")
    
    # Return all environment variables relevant to the application
    env_vars = {}
    for var in REQUIRED_ENV_VARS + list(DEFAULT_ENV_VARS.keys()):
        env_vars[var] = os.getenv(var)
    
    return env_vars

def get_reddit_instance(bot_username: str) -> praw.Reddit:
    """
    Get a Reddit instance for the specified bot using praw.ini configuration.
    
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

def init_configuration() -> Dict[str, Any]:
    """
    Initialize and validate all configuration for the application.
    
    Returns:
        Dict[str, Any]: Configuration dictionary with all settings
    """
    # Load and validate environment variables
    env_vars = validate_environment()
    
    # Create a configuration dictionary
    config = {
        "openai": {
            "api_key": env_vars["OPENAI_API_KEY"],
            "model": env_vars["LLM_MODEL"],
            "temperature": float(env_vars["LLM_TEMPERATURE"]),
            "max_tokens": int(env_vars["LLM_MAX_TOKENS"]),
        },
        "features": {
            "thread_analysis": env_vars["ENABLE_THREAD_ANALYSIS"].lower() == "true",
            "humanization": env_vars["ENABLE_HUMANIZATION"].lower() == "true",
        },
        "runtime": {
            "dry_run": env_vars["DRY_RUN"].lower() == "true",
            "bot_username": env_vars["BOT_USERNAME"],
        }
    }
    
    return config

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
        try:
            config = init_configuration()
            print("Configuration validation successful!")
            print("Current configuration:")
            for section, values in config.items():
                print(f"\n[{section}]")
                for key, value in values.items():
                    print(f"{key}: {value}")
        except ValueError as e:
            print(f"Configuration error: {e}") 