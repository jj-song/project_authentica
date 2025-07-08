#!/usr/bin/env python3
"""
View comments on a specific Reddit post.
"""

import sys
import os
import praw

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import get_reddit_instance

def main():
    """View comments on a specific post."""
    # Get Reddit instance
    reddit = get_reddit_instance("my_first_bot")
    print(f"Authenticated as {reddit.user.me()}")
    
    # Get the submission
    submission_id = "1lu9d24"  # ID of our test post
    submission = reddit.submission(submission_id)
    
    print(f"\nPost Title: {submission.title}")
    print(f"Post Content: {submission.selftext}")
    
    # Get and display comments
    submission.comments.replace_more(limit=0)  # Fetch all comments
    print("\n--- Comments ---")
    for comment in submission.comments:
        print(f"Author: {comment.author}")
        print(f"Comment: {comment.body}")
        print("-" * 50)

if __name__ == "__main__":
    main() 