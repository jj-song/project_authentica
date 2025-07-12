#!/usr/bin/env python3
"""
Reddit utility functions for Project Authentica.
Provides centralized Reddit API operations and error handling.
"""

import logging
import praw
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from typing import Optional, Dict, Any, List, Union
from praw.models import Submission, Comment

# Configure logging
logger = logging.getLogger(__name__)

def get_reddit_instance(username: str) -> praw.Reddit:
    """
    Get an authenticated Reddit instance for a specific bot username.
    Uses praw.ini for configuration.
    
    Args:
        username (str): Bot username to authenticate as
        
    Returns:
        praw.Reddit: Authenticated Reddit instance
    
    Raises:
        ValueError: If authentication fails
    """
    try:
        reddit = praw.Reddit(username)
        # Verify authentication
        user = reddit.user.me()
        if user is None:
            raise ValueError(f"Failed to authenticate as {username}")
        if str(user) != username:
            logger.warning(f"Authenticated as {user} instead of requested {username}")
        
        logger.info(f"Successfully authenticated as {user}")
        return reddit
    except Exception as e:
        logger.error(f"Reddit authentication error: {str(e)}")
        raise ValueError(f"Failed to authenticate as {username}: {str(e)}")

def check_shadowban(reddit: praw.Reddit) -> bool:
    """
    Check if the authenticated Reddit user is shadowbanned.
    
    Args:
        reddit (praw.Reddit): Authenticated Reddit instance
        
    Returns:
        bool: True if the user appears to be shadowbanned, False otherwise
    """
    try:
        username = str(reddit.user.me())
        user = reddit.redditor(username)
        
        # Try to access the user's profile
        # If shadowbanned, this will raise a 404 error
        _ = user.created_utc
        
        # Check if user's most recent comments are visible
        comments = list(user.comments.new(limit=3))
        for comment in comments:
            # Force a fetch of the comment to check if it's accessible
            try:
                fetched = reddit.comment(id=comment.id)
                fetched.refresh()
                if fetched.author is None:
                    return True  # Comment exists but author shows as [deleted]
            except Exception:
                return True  # Comment not accessible
                
        return False  # User appears to be in good standing
    except Exception as e:
        logger.error(f"Error checking shadowban status: {str(e)}")
        # If we can't check, assume shadowbanned to be safe
        return True

def check_shadowban_by_username(username: str) -> bool:
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
        logger.error(f"Request timed out while checking shadowban status for {username}")
        # We can't determine if shadowbanned, so return False as a safe default
        return False
        
    except ConnectionError:
        logger.error(f"Connection error while checking shadowban status for {username}")
        # We can't determine if shadowbanned, so return False as a safe default
        return False
        
    except RequestException as e:
        logger.error(f"Request error while checking shadowban status for {username}: {str(e)}")
        # We can't determine if shadowbanned, so return False as a safe default
        return False

def get_submission(reddit: praw.Reddit, submission_id: str) -> Optional[Submission]:
    """
    Get a Reddit submission by ID with error handling.
    
    Args:
        reddit (praw.Reddit): Authenticated Reddit instance
        submission_id (str): ID of the submission to fetch
        
    Returns:
        Optional[Submission]: The submission object or None if not found
    """
    try:
        submission = reddit.submission(id=submission_id)
        # Force a fetch to verify the submission exists
        _ = submission.title
        return submission
    except Exception as e:
        logger.error(f"Error fetching submission {submission_id}: {str(e)}")
        return None

def get_comment(reddit: praw.Reddit, comment_id: str) -> Optional[Comment]:
    """
    Get a Reddit comment by ID with error handling.
    
    Args:
        reddit (praw.Reddit): Authenticated Reddit instance
        comment_id (str): ID of the comment to fetch
        
    Returns:
        Optional[Comment]: The comment object or None if not found
    """
    try:
        comment = reddit.comment(id=comment_id)
        # Force a fetch to verify the comment exists
        comment.refresh()
        return comment
    except Exception as e:
        logger.error(f"Error fetching comment {comment_id}: {str(e)}")
        return None 