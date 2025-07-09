#!/usr/bin/env python3
"""
Run the Authentica agent once without the scheduler.
This script is for testing the enhanced features.
"""

import sys
import os
import logging
import json
import praw
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_db_connection, initialize_database
from src.config import get_reddit_instance
from src.agent import KarmaAgent
from src.context.collector import ContextCollector
from src.context.templates import TemplateSelector, VariationEngine
from src.llm_handler import generate_comment_from_submission

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AuthenticaOneShot")

# Bot configuration
BOT_USERNAME = "my_first_bot"
TARGET_SUBREDDIT = 'formula1'  # Using Formula 1 subreddit
POST_LIMIT = 1  # Only process 1 post

def main():
    """Run the agent once to post a comment with all new features."""
    logger.info("Starting one-time run of Project Authentica...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        initialize_database()
        
        # Get database connection
        db_conn = get_db_connection()
        logger.info("Database connection established")
        
        # Get Reddit instance
        logger.info(f"Authenticating as {BOT_USERNAME}...")
        reddit = get_reddit_instance(BOT_USERNAME)
        logger.info(f"Successfully authenticated as {reddit.user.me()}")
        
        # Create context collector to inspect what we're gathering
        collector = ContextCollector(reddit)
        
        # Create agent
        agent = KarmaAgent(reddit, db_conn)
        logger.info("KarmaAgent initialized")
        
        # First get a suitable post to analyze
        logger.info(f"Finding a suitable post in r/{TARGET_SUBREDDIT}...")
        subreddit = reddit.subreddit(TARGET_SUBREDDIT)
        
        # Get posts from different sort methods to find an unlocked one
        posts = []
        posts.extend(list(subreddit.new(limit=5)))
        posts.extend(list(subreddit.rising(limit=5)))
        posts.extend(list(subreddit.hot(limit=10)))
        
        # Find a suitable post (non-stickied, with comments, not locked)
        suitable_post = None
        for post in posts:
            if not post.stickied and post.num_comments > 2 and not post.locked:
                try:
                    # Try to get comments to verify it's not locked
                    post.comments.replace_more(limit=0)
                    if len(post.comments) > 0:
                        suitable_post = post
                        break
                except Exception as e:
                    logger.info(f"Skipping post {post.id}: {str(e)}")
                    continue
        
        if not suitable_post:
            logger.error("No suitable posts found in r/formula1. Exiting.")
            return
        
        # Collect and print context for the selected post
        logger.info(f"Selected post: '{suitable_post.title}'")
        context = collector.collect_context(suitable_post)
        
        # Print important context factors
        print("\n=== IMPORTANT CONTEXT FACTORS ===\n")
        print(f"Post Title: {context['submission']['title']}")
        print(f"Post Score: {context['submission']['score']}")
        print(f"Post Author: {context['submission']['author']}")
        print(f"Number of Comments: {context['submission']['num_comments']}")
        print(f"Subreddit: r/{context['subreddit']['name']}")
        print(f"Subreddit Description: {context['subreddit']['description']}")
        print(f"Subreddit Subscribers: {context['subreddit']['subscribers']}")
        print(f"Day of Week: {context['temporal']['day_of_week']}")
        print(f"Hour of Day: {context['temporal']['hour_of_day']}")
        
        # Print top comments for context
        print("\n=== TOP COMMENTS USED FOR CONTEXT ===\n")
        for i, comment in enumerate(context['comments'][:3], 1):
            print(f"Comment {i} (Score: {comment['score']}):")
            print(f"Author: {comment['author']}")
            print(f"Content: {comment['body'][:150]}..." if len(comment['body']) > 150 else f"Content: {comment['body']}")
            print()
        
        # Show template selection and variations
        template_selector = TemplateSelector()
        selected_template = template_selector.select_template(context)
        print("\n=== TEMPLATE SELECTION ===\n")
        print(f"Selected Template: {selected_template.__class__.__name__}")
        
        variations = VariationEngine.get_random_variations(2)
        print("\n=== SELECTED VARIATIONS ===\n")
        for i, variation in enumerate(variations, 1):
            print(f"Variation {i}: {variation}")
        
        # Generate the comment directly
        print("\n=== GENERATING COMMENT ===\n")
        comment_text = generate_comment_from_submission(suitable_post, reddit)
        print(f"Generated Comment:\n{comment_text}\n")
        
        # Post the comment
        print("\n=== POSTING COMMENT ===\n")
        try:
            # Try to find a suitable comment to reply to
            eligible_comments = [
                comment for comment in suitable_post.comments
                if (comment.score > 0 and 
                    str(comment.author) != agent.username and
                    len(comment.body) >= 20 and
                    comment.author != "AutoModerator")
            ]
            
            if eligible_comments and len(eligible_comments) > 0:
                # Sort by score and select one from the top
                eligible_comments.sort(key=lambda c: c.score, reverse=True)
                selected_comment = eligible_comments[0]
                print(f"Replying to comment by {selected_comment.author}: {selected_comment.body[:100]}...")
                
                # Generate a reply
                reply_text = generate_comment_from_submission(suitable_post, reddit, comment_to_reply=selected_comment)
                print(f"Generated Reply:\n{reply_text}\n")
                
                # Post the reply
                reply = selected_comment.reply(reply_text)
                print(f"Reply posted successfully! Comment ID: {reply.id}")
                print(f"View at: https://www.reddit.com{suitable_post.permalink}{selected_comment.id}/{reply.id}/")
            else:
                # Post directly to the submission
                print("No suitable comments found. Posting directly to submission...")
                comment = suitable_post.reply(comment_text)
                print(f"Comment posted successfully! Comment ID: {comment.id}")
                print(f"View at: https://www.reddit.com{suitable_post.permalink}{comment.id}/")
        
        except Exception as e:
            logger.error(f"Error posting comment: {str(e)}")
            print(f"Error posting comment: {str(e)}")
        
        logger.info("One-time run completed successfully")
        
    except Exception as e:
        logger.error(f"Error in one-time run: {str(e)}")
        raise
        
    finally:
        # Close database connection
        if 'db_conn' in locals():
            logger.info("Closing database connection...")
            db_conn.close()

if __name__ == "__main__":
    main() 