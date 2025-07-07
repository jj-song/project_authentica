#!/usr/bin/env python3
"""
Test script to run a single scan without the scheduler.
"""

import logging
from src.database import get_db_connection, initialize_database
from src.config import get_reddit_instance
from src.agent import KarmaAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestRun")

# Bot configuration
BOT_USERNAME = "my_first_bot"
TARGET_SUBREDDIT = "testingground4bots"
POST_LIMIT = 5

def main():
    """Run a single scan without the scheduler."""
    try:
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
        
        # Run a single scan
        logger.info(f"Running a scan of r/{TARGET_SUBREDDIT}...")
        agent.scan_and_comment(TARGET_SUBREDDIT, POST_LIMIT)
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