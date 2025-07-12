#!/usr/bin/env python3
"""
Main entry point for Project Authentica.
Initializes all components and starts scheduled bot operations.
"""

import logging
import time
import signal
import sys
import os
import random
import datetime
from typing import NoReturn, Optional

from apscheduler.schedulers.background import BackgroundScheduler
import praw

from src.database import get_db_connection, initialize_database
from src.config import get_reddit_instance
from src.agent import KarmaAgent
from src.context.collector import ContextCollector
from src.context.templates import TemplateSelector, VariationEngine
from src.llm_handler import generate_comment_from_submission


# Bot configuration
BOT_USERNAME = "my_first_bot"
TARGET_SUBREDDITS = ['SkincareAddiction', 'testingground4bots', 'formula1']

# Enable thread analysis
os.environ["ENABLE_THREAD_ANALYSIS"] = "true"


def run_once(subreddit_name, post_limit=10, verbose=False):
    """
    Run the bot once on the specified subreddit.
    
    Args:
        subreddit_name (str): The name of the subreddit to run on.
        post_limit (int, optional): The maximum number of posts to process. Defaults to 10.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.
    """
    logger = logging.getLogger("AuthenticaOneShot")
    logger.info(f"Starting one-time run of Project Authentica for r/{subreddit_name}...")
    
    # Initialize database
    logger.info("Initializing database...")
    db_conn = init_db()
    logger.info("Database connection established")
    
    try:
        # Authenticate with Reddit
        logger.info(f"Authenticating as {BOT_USERNAME}...")
        try:
            reddit = get_reddit_instance(BOT_USERNAME)
            logger.info(f"Successfully authenticated as {reddit.user.me().name}")
        except ValueError as e:
            if "banned or suspended" in str(e):
                logger.error(f"ACCOUNT BANNED: {str(e)}")
                print(f"\nERROR: {str(e)}")
                print("Please check your account status on Reddit or try with a different account.")
                return
            else:
                logger.error(f"Authentication error: {str(e)}")
                raise
        
        # Initialize KarmaAgent
        karma_agent = KarmaAgent(reddit, db_conn)
        logger.info("KarmaAgent initialized")
        
        # Find a suitable post in the subreddit
        logger.info(f"Finding a suitable post in r/{subreddit_name}...")
        
        # Get posts from the subreddit
        subreddit = reddit.subreddit(subreddit_name)
        
        # Skip posts if specified
        skip_posts = os.environ.get('SKIP_POSTS', '').split(',')
        
        # Find a suitable post
        selected_post = None
        for post in subreddit.hot(limit=post_limit):
            if post.id in skip_posts:
                continue
            if post.num_comments > 0:
                selected_post = post
                break
        
        if selected_post is None:
            logger.error(f"No suitable posts found in r/{subreddit_name}")
            return
        
        logger.info(f"Selected post: '{selected_post.title}'")
        
        # Collect context
        context = collect_context(selected_post)
        
        # Analyze the thread
        thread_analyzer = ThreadAnalyzer(reddit)
        thread_analysis = thread_analyzer.analyze_thread(selected_post)
        
        # Determine response strategy
        strategy_selector = ResponseStrategySelector(thread_analysis)
        response_strategy = strategy_selector.select_strategy()
        
        # Select a template
        template_selector = TemplateSelector()
        template = template_selector.select_template(response_strategy, context)
        
        # Select variations
        variations = template_selector.select_variations(2)  # Select 2 random variations
        
        # Log the selected strategy and template
        logger.info(f"\n=== SELECTED RESPONSE STRATEGY ===\n")
        logger.info(f"Strategy type: {response_strategy.strategy_type}")
        logger.info(f"Reasoning: {response_strategy.reasoning}")
        if hasattr(response_strategy, 'target_comment') and response_strategy.target_comment:
            logger.info(f"Target comment: {response_strategy.target_comment.id} by {response_strategy.target_comment.author}")
        elif hasattr(response_strategy, 'target') and response_strategy.target:
            logger.info(f"Target: {response_strategy.target}")
        
        logger.info(f"\n=== TEMPLATE SELECTION ===\n")
        logger.info(f"Selected Template: {template.__class__.__name__}")
        
        logger.info(f"\n=== SELECTED VARIATIONS ===\n")
        for i, variation in enumerate(variations, 1):
            logger.info(f"Variation {i}: {variation}")
        
        # Determine which comment to reply to
        target_comment = None
        if hasattr(response_strategy, 'target_comment') and response_strategy.target_comment:
            target_comment = response_strategy.target_comment
        
        # Post a comment
        logger.info(f"\n=== POSTING COMMENT ===\n")
        if target_comment:
            logger.info(f"Replying to comment by {target_comment.author}: {target_comment.body[:100]}...")
            logger.info(f"Comment score: {target_comment.score}")
        else:
            logger.info(f"Posting a top-level comment on '{selected_post.title}'")
        
        # Generate and post the comment
        try:
            llm_handler = LLMHandler()
            
            # Get the comment content
            comment_content = llm_handler.generate_response(
                selected_post,
                target_comment,
                response_strategy,
                template,
                variations,
                context,
                reddit,
                db_conn,
                verbose=verbose
            )
            
            # Post the comment
            if not os.environ.get('DRY_RUN', False):
                try:
                    if target_comment:
                        reply = target_comment.reply(comment_content)
                    else:
                        reply = selected_post.reply(comment_content)
                    
                    logger.info(f"Reply posted successfully! Comment ID: {reply.id}")
                    logger.info(f"View at: {reply.permalink}")
                    
                    # Record the comment in the database
                    karma_agent.record_comment(reply.id, selected_post.id, target_comment.id if target_comment else None)
                except praw.exceptions.RedditAPIException as e:
                    logger.error(f"Error posting comment: {str(e)}")
                    print(f"Error posting comment: {str(e)}")
            else:
                logger.info("DRY RUN: Comment not posted")
                logger.info(f"Generated Reply:\n{comment_content}")
        except Exception as e:
            logger.error(f"Error generating or posting comment: {str(e)}")
            raise
        
        logger.info("One-time run completed successfully")
    except Exception as e:
        logger.error(f"Error in one-time run: {str(e)}")
        raise
    finally:
        # Close database connection
        logger.info("Closing database connection...")
        if db_conn:
            db_conn.close()


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
    logger.info("Starting Project Authentica with advanced thread analysis...")
    
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
        
        # Create context collector for enhanced context gathering
        collector = ContextCollector(reddit)
        logger.info("Context collector initialized")
        
        # Create agent
        agent = KarmaAgent(reddit, db_conn)
        logger.info("KarmaAgent initialized")
        
        # Initialize thread analysis if available
        try:
            from src.thread_analysis.analyzer import ThreadAnalyzer
            from src.thread_analysis.strategies import ResponseStrategy
            logger.info("Thread analysis modules loaded successfully")
        except ImportError:
            logger.warning("Thread analysis modules not available. Some advanced features will be disabled.")
        
        # Initialize scheduler
        logger.info("Setting up scheduler...")
        scheduler = BackgroundScheduler(timezone='UTC')
        
        # Add jobs to scan different subreddits
        for i, target_subreddit in enumerate(TARGET_SUBREDDITS):
            # Stagger the schedules to avoid all running at once
            offset_minutes = i * 10  # 10 minutes between each subreddit
            
            scheduler.add_job(
                agent.scan_and_comment,
                'interval',
                minutes=30,
                jitter=300,  # Add random jitter of up to 5 minutes
                args=[target_subreddit, 10],  # Subreddit name and post limit
                id=f'scan_job_{target_subreddit}',
                name=f'Scan r/{target_subreddit}',
                next_run_time=time.time() + (offset_minutes * 60)  # Staggered start
            )
            logger.info(f"Scheduled job to scan r/{target_subreddit} every ~30 minutes (offset: {offset_minutes} min)")
        
        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler started with all jobs")
        
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
    # Check if we should run once or start the scheduler
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Parse additional arguments
        subreddit = 'formula1'  # Default subreddit
        post_limit = 1  # Default post limit
        verbose = True  # Default verbose mode
        
        # Parse subreddit argument
        if len(sys.argv) > 2:
            subreddit = sys.argv[2]
        
        # Parse post limit argument
        if len(sys.argv) > 3:
            try:
                post_limit = int(sys.argv[3])
            except ValueError:
                print(f"Invalid post limit: {sys.argv[3]}. Using default: 1")
        
        # Parse verbose argument
        if len(sys.argv) > 4 and sys.argv[4].lower() == "false":
            verbose = False
        
        # Run once with the specified arguments
        run_once(subreddit, post_limit, verbose)
    else:
        # Start the scheduler
        main()
