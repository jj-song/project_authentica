#!/usr/bin/env python3
"""
Script to check the comment on our test post.
"""

import praw
from src.config import get_reddit_instance

# Post ID from the previous run
POST_ID = '1lu5snp'

def main():
    """Check the comment on our test post."""
    # Get Reddit instance
    reddit = get_reddit_instance('my_first_bot')
    
    # Get the post
    post = reddit.submission(POST_ID)
    
    # Print post details
    print(f"Post title: {post.title}")
    print(f"Post body: {post.selftext}")
    print("\nComments:")
    
    # Get all comments
    post.comments.replace_more(limit=0)  # Ensure all comments are loaded
    for comment in post.comments:
        print(f"Author: {comment.author}")
        print(f"Comment: {comment.body}")
        print("-" * 50)

if __name__ == "__main__":
    main() 