#!/usr/bin/env python3
"""
Script to test the bot with OpenAI integration on the testingground4bots subreddit.
"""

import os
import logging
from dotenv import load_dotenv
from src.database import get_db_connection
from src.config import get_reddit_instance
from src.agent import KarmaAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestBotRun")

# Bot configuration
BOT_USERNAME = "my_first_bot"
TARGET_SUBREDDIT = "testingground4bots"
POST_LIMIT = 5  # Increased to 5 posts for testing

def main():
    """Run a single scan of the testingground4bots subreddit."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Check if API key is set
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY environment variable is not set.")
            logger.error("The bot will use placeholder comments instead of AI-generated ones.")
        
        # Initialize database connection
        logger.info("Getting database connection...")
        db_conn = get_db_connection()
        
        # Get Reddit instance
        logger.info(f"Authenticating as {BOT_USERNAME}...")
        reddit = get_reddit_instance(BOT_USERNAME)
        logger.info(f"Successfully authenticated as {reddit.user.me()}")
        
        # Create agent
        agent = KarmaAgent(reddit, db_conn)
        logger.info("KarmaAgent initialized")
        
        # Run a single scan using 'new' instead of 'hot'
        logger.info(f"Running a scan of r/{TARGET_SUBREDDIT} (new posts)...")
        agent.scan_and_comment(TARGET_SUBREDDIT, POST_LIMIT, sort='new')
        logger.info(f"Scan completed for r/{TARGET_SUBREDDIT}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        # Close database connection
        if 'db_conn' in locals():
            logger.info("Closing database connection...")
            db_conn.close()

if __name__ == "__main__":
    main() 