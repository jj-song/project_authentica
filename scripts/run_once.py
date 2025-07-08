#!/usr/bin/env python3
"""
Run the Authentica agent once without the scheduler.
This script is for testing the enhanced features.
"""

import sys
import os
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_db_connection, initialize_database
from src.config import get_reddit_instance
from src.agent import KarmaAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AuthenticaOneShot")

# Bot configuration
BOT_USERNAME = "my_first_bot"
TARGET_SUBREDDIT = 'testingground4bots'  # Using test subreddit for safety

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
        
        # Create agent
        agent = KarmaAgent(reddit, db_conn)
        logger.info("KarmaAgent initialized")
        
        # Run a single scan with 'new' sort to find fresh posts
        logger.info(f"Running a scan of r/{TARGET_SUBREDDIT} with 'new' sort...")
        agent.scan_and_comment(TARGET_SUBREDDIT, 10, sort='new')  # Scan 10 new posts
        
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