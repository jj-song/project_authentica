#!/usr/bin/env python3
"""
Utility functions for Project Authentica.
Contains helper functions used across the project.
"""

import logging
from typing import Optional, Dict, Any, Union, List, Tuple, Set, Callable, bool
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


def check_shadowban(username: str) -> bool:
    """
    Check if a Reddit user is shadowbanned by making an unauthenticated request to their profile.
    
    A shadowbanned user's profile will return a 404 status code when accessed without authentication,
    even though the account still exists. This is different from a deleted or suspended account,
    which would show specific messages.
    
    Args:
        username (str): The Reddit username to check, without the 'u/' prefix.
        
    Returns:
        bool: True if the user appears to be shadowbanned (404 response),
              False if the profile is publicly visible.
              
    Raises:
        ValueError: If the username is empty or invalid.
        
    Example:
        >>> is_banned = check_shadowban("username")
        >>> print(f"Is shadowbanned: {is_banned}")
    """
    # Validate username
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")
    
    # Remove 'u/' prefix if present
    clean_username = username.strip()
    if clean_username.startswith('u/'):
        clean_username = clean_username[2:]
    
    # Construct the profile URL
    profile_url = f"https://www.reddit.com/user/{clean_username}"
    
    # Set a custom User-Agent to avoid Reddit's rate limiting
    headers = {
        "User-Agent": "Mozilla/5.0 (Project Authentica Shadowban Checker)"
    }
    
    try:
        # Make the request with a timeout
        response = requests.get(profile_url, headers=headers, timeout=10)
        
        # Check if the status code is 404 (shadowbanned)
        return response.status_code == 404
        
    except Timeout:
        logging.error(f"Request timed out while checking shadowban status for {username}")
        # We can't determine if shadowbanned, so return False as a safe default
        return False
        
    except ConnectionError:
        logging.error(f"Connection error while checking shadowban status for {username}")
        # We can't determine if shadowbanned, so return False as a safe default
        return False
        
    except RequestException as e:
        logging.error(f"Request error while checking shadowban status for {username}: {str(e)}")
        # We can't determine if shadowbanned, so return False as a safe default
        return False


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        test_username = sys.argv[1]
        try:
            result = check_shadowban(test_username)
            print(f"Username: {test_username}")
            print(f"Shadowbanned: {result}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python utils.py <username>") 