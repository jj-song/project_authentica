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


def run_once(subreddit_name: str = 'formula1', post_limit: int = 1, verbose: bool = True) -> None:
    """
    Run the Authentica agent once without the scheduler.
    
    This function:
    1. Initializes database and connections
    2. Finds a suitable post in the specified subreddit
    3. Analyzes the post and generates a comment
    4. Posts the comment
    
    Args:
        subreddit_name (str): Name of the subreddit to scan (without the 'r/' prefix)
        post_limit (int): Maximum number of posts to process
        verbose (bool): Whether to print detailed information about the process
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("AuthenticaOneShot")
    
    logger.info(f"Starting one-time run of Project Authentica for r/{subreddit_name}...")
    
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
        logger.info(f"Finding a suitable post in r/{subreddit_name}...")
        subreddit = reddit.subreddit(subreddit_name)
        
        # Get posts from different sort methods to find an unlocked one
        posts = []
        posts.extend(list(subreddit.new(limit=5)))
        posts.extend(list(subreddit.rising(limit=5)))
        posts.extend(list(subreddit.hot(limit=10)))
        
        # Find a suitable post (non-stickied, with comments, not locked)
        suitable_posts = []
        for post in posts:
            if not post.stickied and post.num_comments > 2 and not post.locked:
                try:
                    # Try to get comments to verify it's not locked
                    post.comments.replace_more(limit=0)
                    if len(post.comments) > 0:
                        suitable_posts.append(post)
                        if len(suitable_posts) >= post_limit:
                            break
                except Exception as e:
                    logger.info(f"Skipping post {post.id}: {str(e)}")
                    continue
        
        if not suitable_posts:
            logger.error(f"No suitable posts found in r/{subreddit_name}. Exiting.")
            return
        
        for suitable_post in suitable_posts:
            # Collect and print context for the selected post
            logger.info(f"Selected post: '{suitable_post.title}'")
            context = collector.collect_context(suitable_post)
            
            if verbose:
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
            
            # Perform thread analysis
            try:
                from src.thread_analysis.analyzer import ThreadAnalyzer
                from src.thread_analysis.strategies import ResponseStrategy
                
                # Create thread analyzer
                analyzer = ThreadAnalyzer(reddit)
                
                # Perform analysis
                if verbose:
                    print("\n=== PERFORMING ADVANCED THREAD ANALYSIS ===\n")
                thread_analysis = analyzer.analyze_thread(suitable_post)
                
                if verbose:
                    # Print basic stats
                    print(f"Comment count: {thread_analysis['comment_count']}")
                    print(f"Thread depth: {thread_analysis['thread_depth']}")
                    print(f"Key topics: {', '.join(thread_analysis['key_topics'])}")
                
                # Generate response strategy
                strategy_generator = ResponseStrategy()
                strategy = strategy_generator.determine_strategy(thread_analysis, context)
                
                if verbose:
                    # Print strategy
                    print("\n=== SELECTED RESPONSE STRATEGY ===\n")
                    print(f"Strategy type: {strategy['type']}")
                    print(f"Reasoning: {strategy['reasoning']}")
                    
                    if strategy['target_comment']:
                        print(f"Target comment: {strategy['target_comment']['id']} by {strategy['target_comment']['author']}")
                    else:
                        print("Target: Direct reply to submission")
            except ImportError:
                if verbose:
                    print("\nThread analysis modules not available. Skipping advanced analysis.")
            except Exception as e:
                if verbose:
                    print(f"\nError in thread analysis: {str(e)}")
            
            if verbose:
                # Show template selection and variations
                template_selector = TemplateSelector()
                selected_template = template_selector.select_template(context)
                print("\n=== TEMPLATE SELECTION ===\n")
                print(f"Selected Template: {selected_template.__class__.__name__}")
                
                variations = VariationEngine.get_random_variations(2)
                print("\n=== SELECTED VARIATIONS ===\n")
                for i, variation in enumerate(variations, 1):
                    print(f"Variation {i}: {variation}")
            
            # Post the comment
            if verbose:
                print("\n=== POSTING COMMENT ===\n")
            try:
                # Replace MoreComments objects to get a flattened comment tree
                suitable_post.comments.replace_more(limit=0)
                
                # Filter for comments that:
                # 1. Have a positive score
                # 2. Are not from the bot itself
                # 3. Have some substance (not too short)
                eligible_comments = [
                    comment for comment in suitable_post.comments
                    if (comment.score > 0 and 
                        str(comment.author) != agent.username and
                        len(comment.body) >= 20)
                ]
                
                if eligible_comments:
                    # Sort by score and select a comment from the top 3 (if available)
                    eligible_comments.sort(key=lambda c: c.score, reverse=True)
                    top_comments = eligible_comments[:min(3, len(eligible_comments))]
                    selected_comment = random.choice(top_comments)
                    
                    if verbose:
                        print(f"Replying to comment by {selected_comment.author}: {selected_comment.body[:100]}...")
                        print(f"Comment score: {selected_comment.score}")
                    
                    # Generate a reply using context-aware LLM handler
                    reply_text = generate_comment_from_submission(suitable_post, reddit, comment_to_reply=selected_comment)
                    
                    if verbose:
                        print(f"Generated Reply:\n{reply_text}\n")
                    
                    # Post the reply
                    reply = selected_comment.reply(reply_text)
                    
                    if verbose:
                        print(f"Reply posted successfully! Comment ID: {reply.id}")
                        print(f"View at: https://www.reddit.com{suitable_post.permalink}{selected_comment.id}/{reply.id}/")
                    
                    # Create a record in comment_performance table
                    current_time = datetime.datetime.now().isoformat()
                    cursor = db_conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO comment_performance 
                        (comment_id, submission_id, subreddit, initial_score, current_score, last_checked) 
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (reply.id, suitable_post.id, subreddit_name, 1, 1, current_time)
                    )
                    db_conn.commit()
                else:
                    # No suitable comments found, post directly to the submission
                    if verbose:
                        print("No suitable comments found. Posting directly to submission...")
                    
                    # Generate the comment directly
                    comment_text = generate_comment_from_submission(suitable_post, reddit)
                    
                    if verbose:
                        print(f"Generated Comment:\n{comment_text}\n")
                    
                    # Post the comment
                    comment = suitable_post.reply(comment_text)
                    
                    if verbose:
                        print(f"Comment posted successfully! Comment ID: {comment.id}")
                        print(f"View at: https://www.reddit.com{suitable_post.permalink}{comment.id}/")
                    
                    # Create a record in comment_performance table
                    current_time = datetime.datetime.now().isoformat()
                    cursor = db_conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO comment_performance 
                        (comment_id, submission_id, subreddit, initial_score, current_score, last_checked) 
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (comment.id, suitable_post.id, subreddit_name, 1, 1, current_time)
                    )
                    db_conn.commit()
            
            except Exception as e:
                logger.error(f"Error posting comment: {str(e)}")
                if verbose:
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
