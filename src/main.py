#!/usr/bin/env python3
"""
Main entry point for Project Authentica.
Initializes all components and starts scheduled bot operations.
"""

import logging
import time
import signal
import sys
from typing import NoReturn

from apscheduler.schedulers.background import BackgroundScheduler

from src.database import get_db_connection, initialize_database
from src.config import get_reddit_instance
from src.agent import KarmaAgent


# Bot configuration
BOT_USERNAME = "my_first_bot"
TARGET_SUBREDDITS = ['SkincareAddiction', 'testingground4bots']


def main() -> NoReturn:
    """
    Initialize all components and start the scheduled bot operations.
    
    This function:
    1. Sets up logging
    2. Initializes the database
    3. Creates connections to Reddit API and database
    4. Sets up a background scheduler for periodic tasks
    5. Keeps the main thread alive while the scheduler runs
    
    Returns:
        NoReturn: This function runs indefinitely until interrupted
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("AuthenticalMain")
    
    # Print startup message
    logger.info("Starting Project Authentica...")
    
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
        
        # Initialize scheduler
        logger.info("Setting up scheduler...")
        scheduler = BackgroundScheduler(timezone='UTC')
        
        # Add job to scan subreddits
        target_subreddit = TARGET_SUBREDDITS[0]  # Use the first subreddit in the list
        scheduler.add_job(
            agent.scan_and_comment,
            'interval',
            minutes=30,
            jitter=300,  # Add random jitter of up to 5 minutes
            args=[target_subreddit, 10],  # Subreddit name and post limit
            id='scan_job',
            name=f'Scan r/{target_subreddit}'
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info(f"Scheduler started. Will scan r/{target_subreddit} every ~30 minutes")
        
        # Set up signal handling for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received. Cleaning up...")
            scheduler.shutdown()
            db_conn.close()
            logger.info("Cleanup complete. Exiting.")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Keep the main thread alive
        logger.info("Bot is now running. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise
        
    finally:
        # Ensure scheduler is shut down
        if 'scheduler' in locals() and scheduler.running:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
        
        # Close database connection
        if 'db_conn' in locals():
            logger.info("Closing database connection...")
            db_conn.close()


if __name__ == "__main__":
    main() 