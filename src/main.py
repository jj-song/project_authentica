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
import argparse
import json
from typing import NoReturn, Optional

from apscheduler.schedulers.background import BackgroundScheduler
import praw
from praw.exceptions import PRAWException, APIException, ClientException

from src.database import get_db_connection, initialize_database
from src.config import get_reddit_instance
from src.agent import KarmaAgent
from src.context.collector import ContextCollector
from src.context.templates import TemplateSelector, VariationEngine
from src.llm_handler import generate_comment_from_submission
from src.thread_analysis.analyzer import ThreadAnalyzer
from src.thread_analysis.strategies import ResponseStrategy


# Bot configuration
BOT_USERNAME = "my_first_bot"
TARGET_SUBREDDITS = ['SkincareAddiction', 'testingground4bots', 'formula1']

# Enable thread analysis by default
os.environ["ENABLE_THREAD_ANALYSIS"] = "true"


def parse_arguments():
    """Parse command line arguments for Project Authentica."""
    parser = argparse.ArgumentParser(
        description='Project Authentica - Reddit bot with advanced context awareness and thread analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Main operation mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--once', action='store_true',
                        help='Run the bot once without scheduling')
    mode_group.add_argument('--schedule', action='store_true',
                        help='Run the bot with the scheduler (default)')
    
    # Target parameters
    parser.add_argument('--subreddit', '-s', type=str, default='formula1',
                        help='Subreddit to scan (default: formula1)')
    parser.add_argument('--limit', '-l', type=int, default=1,
                        help='Maximum number of posts to process (default: 1)')
    parser.add_argument('--sort', type=str, choices=['hot', 'new', 'top', 'rising'], default='hot',
                       help='Sort method for posts (default: hot)')
    
    # Scheduler options (when using --schedule)
    parser.add_argument('--interval', type=int, default=30,
                       help='Minutes between scheduled runs (default: 30)')
    parser.add_argument('--jitter', type=int, default=5,
                       help='Random jitter in minutes to add to interval (default: 5)')
    
    # Utility options
    parser.add_argument('--check-comment', type=str, metavar='COMMENT_ID',
                       help='Check status and performance of a specific comment')
    parser.add_argument('--show-context', type=str, metavar='SUBMISSION_ID',
                       help='Show context collected for a specific submission')
    parser.add_argument('--view-comments', type=str, metavar='SUBMISSION_ID',
                       help='View comments on a specific submission')
    
    # Debug and development options
    parser.add_argument('--dry-run', action='store_true',
                       help='Generate but do not post comments')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with additional logging')
    
    return parser.parse_args()


def run_once(subreddit_name, post_limit=10, sort='hot', verbose=False):
    """
    Run the bot once on the specified subreddit.
    
    Args:
        subreddit_name (str): The name of the subreddit to run on.
        post_limit (int, optional): The maximum number of posts to process. Defaults to 10.
        sort (str, optional): Sort method for posts ('hot', 'new', 'top', 'rising'). Defaults to 'hot'.
        verbose (bool, optional): Whether to print verbose output. Defaults to False.
    """
    logger = logging.getLogger("AuthenticaOneShot")
    logger.info(f"Starting one-time run of Project Authentica for r/{subreddit_name}...")
    
    # Initialize database
    logger.info("Initializing database...")
    initialize_database()
    db_conn = get_db_connection()
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
        
        # Get posts based on sort method
        if sort == 'hot':
            posts = subreddit.hot(limit=post_limit)
        elif sort == 'new':
            posts = subreddit.new(limit=post_limit)
        elif sort == 'top':
            posts = subreddit.top(limit=post_limit)
        elif sort == 'rising':
            posts = subreddit.rising(limit=post_limit)
        else:
            posts = subreddit.hot(limit=post_limit)
            logger.warning(f"Invalid sort method '{sort}', using 'hot' instead")
        
        # Skip posts if specified
        skip_posts = os.environ.get('SKIP_POSTS', '').split(',')
        
        # Find a suitable post
        selected_post = None
        for post in posts:
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
        collector = ContextCollector(reddit)
        context = collector.collect_context(selected_post)
        
        # Analyze the thread
        thread_analyzer = ThreadAnalyzer(reddit)
        thread_analysis = thread_analyzer.analyze_thread(selected_post)

        # Determine response strategy
        strategy = ResponseStrategy()
        response_strategy = strategy.determine_strategy(thread_analysis, context)

        # Select a template
        template_selector = TemplateSelector()
        template = template_selector.select_template(response_strategy, context)

        # Select variations
        variations = VariationEngine.get_random_variations(2)  # Select 2 random variations

        # Log the selected strategy and template
        logger.info(f"\n=== SELECTED RESPONSE STRATEGY ===\n")
        logger.info(f"Strategy type: {response_strategy['type']}")
        logger.info(f"Reasoning: {response_strategy['reasoning']}")
        if response_strategy.get('target_comment'):
            logger.info(f"Target comment: {response_strategy['target_comment'].get('id')} by {response_strategy['target_comment'].get('author')}")
        elif response_strategy.get('target'):
            logger.info(f"Target: {response_strategy['target']}")

        logger.info(f"\n=== TEMPLATE SELECTION ===\n")
        logger.info(f"Selected Template: {template.__class__.__name__}")

        logger.info(f"\n=== SELECTED VARIATIONS ===\n")
        for i, variation in enumerate(variations, 1):
            logger.info(f"Variation {i}: {variation}")
        
        # Determine which comment to reply to
        target_comment = None
        if response_strategy.get('target_comment'):
            # Find the actual comment object in the submission
            for comment in selected_post.comments.list():
                if hasattr(comment, "id") and comment.id == response_strategy['target_comment'].get('id'):
                    target_comment = comment
                    break
        
        # Post a comment
        logger.info(f"\n=== POSTING COMMENT ===\n")
        if target_comment:
            logger.info(f"Replying to comment by {target_comment.author}: {target_comment.body[:100]}...")
            logger.info(f"Comment score: {target_comment.score}")
        else:
            logger.info(f"Posting a top-level comment on '{selected_post.title}'")
        
        # Generate and post the comment
        try:
            # Get the comment content
            comment_content = generate_comment_from_submission(
                selected_post,
                reddit,
                variation_count=2,
                comment_to_reply=target_comment,
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


def run_scheduled(subreddit_names, post_limit=10, interval_minutes=30, jitter_minutes=5, verbose=False):
    """
    Run the bot with a scheduler.
    
    Args:
        subreddit_names (list): List of subreddit names to scan
        post_limit (int): Maximum number of posts to process per subreddit
        interval_minutes (int): Minutes between scheduled runs
        jitter_minutes (int): Random jitter in minutes to add to interval
        verbose (bool): Whether to print verbose output
    """
    logger = logging.getLogger("AuthenticalScheduled")
    
    # Print startup message
    logger.info("Starting Project Authentica with scheduler...")
    
    # Initialize database
    logger.info("Initializing database...")
    initialize_database()
    db_conn = get_db_connection()
    logger.info("Database connection established")
    
    try:
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
        
        # Add jobs to scan different subreddits
        for i, subreddit_name in enumerate(subreddit_names):
            # Stagger the schedules to avoid all running at once
            offset_minutes = i * 10  # 10 minutes between each subreddit
            
            scheduler.add_job(
                agent.scan_and_comment,
                'interval',
                minutes=interval_minutes,
                jitter=jitter_minutes * 60,  # Convert jitter to seconds
                args=[subreddit_name, post_limit],  # Subreddit name and post limit
                id=f'scan_job_{subreddit_name}',
                name=f'Scan r/{subreddit_name}',
                next_run_time=time.time() + (offset_minutes * 60)  # Staggered start
            )
            logger.info(f"Scheduled job to scan r/{subreddit_name} every ~{interval_minutes} minutes (offset: {offset_minutes} min)")
        
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
        logger.error(f"Error in scheduler: {str(e)}")
        raise
        
    finally:
        # Ensure scheduler is shut down
        if 'scheduler' in locals() and scheduler.running:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
        
        # Close database connection
        if db_conn:
            logger.info("Closing database connection...")
            db_conn.close()


def check_comment_status(comment_id, verbose=False):
    """
    Check the status and performance of a specific comment.
    
    Args:
        comment_id (str): The Reddit ID of the comment to check
        verbose (bool): Whether to show detailed information
    """
    logger = logging.getLogger("CommentChecker")
    logger.info(f"Checking status of comment {comment_id}")
    
    # Initialize database connection
    initialize_database()
    db_conn = get_db_connection()
    
    try:
        # Get Reddit instance
        reddit = get_reddit_instance(BOT_USERNAME)
        
        # Get the comment from Reddit
        comment = reddit.comment(id=comment_id)
        comment.refresh()  # Make sure we have the latest data
        
        # Display basic information
        print(f"\nComment ID: {comment_id}")
        print(f"Author: {comment.author}")
        print(f"Current Score: {comment.score}")
        print(f"Permalink: {comment.permalink}")
        print(f"Created: {datetime.datetime.fromtimestamp(comment.created_utc)}")
        
        # Get performance data from database
        cursor = db_conn.cursor()
        cursor.execute(
            "SELECT * FROM comment_performance WHERE comment_id = ?", 
            (comment_id,)
        )
        perf_data = cursor.fetchone()
        
        if perf_data:
            print("\nPerformance Data:")
            print(f"Initial Score: {perf_data['initial_score']}")
            print(f"Last Recorded Score: {perf_data['current_score']}")
            print(f"Last Checked: {perf_data['last_checked']}")
            print(f"Score Change: {perf_data['current_score'] - perf_data['initial_score']}")
        else:
            print("\nNo performance data found in database.")
        
        # Show comment content
        print("\nComment Content:")
        print(comment.body)
        
        if verbose:
            # Get the submission the comment was made on
            submission = comment.submission
            
            print("\nSubmission Details:")
            print(f"Title: {submission.title}")
            print(f"Author: {submission.author}")
            print(f"Score: {submission.score}")
            print(f"Comment Count: {submission.num_comments}")
            
            # Show parent comment if this is a reply
            if comment.parent_id.startswith('t1_'):
                parent = reddit.comment(id=comment.parent_id[3:])
                print("\nParent Comment:")
                print(f"Author: {parent.author}")
                print(f"Score: {parent.score}")
                print(f"Content: {parent.body[:200]}..." if len(parent.body) > 200 else parent.body)
        
    except Exception as e:
        logger.error(f"Error checking comment {comment_id}: {str(e)}")
    finally:
        # Close database connection
        db_conn.close()


def show_submission_context(submission_id, verbose=False):
    """
    Show the context collected for a specific submission.
    
    Args:
        submission_id (str): The Reddit ID of the submission
        verbose (bool): Whether to show detailed information
    """
    logger = logging.getLogger("ContextViewer")
    logger.info(f"Showing context for submission {submission_id}")
    
    try:
        # Get Reddit instance
        reddit = get_reddit_instance(BOT_USERNAME)
        print(f"Authenticated as {reddit.user.me()}")
        
        # Get the submission
        submission = reddit.submission(id=submission_id)
        
        print(f"\nCollecting context for submission: {submission.title}")
        
        # Create context collector and collect context
        collector = ContextCollector(reddit)
        context = collector.collect_context(submission)
        
        # Print the context in a readable format
        print("\n=== COLLECTED CONTEXT ===\n")
        print(json.dumps(context, indent=2))
        
        # Show what templates would be selected
        selector = TemplateSelector()
        template = selector.select_template(context)
        
        print(f"\n=== SELECTED TEMPLATE ===\n")
        print(f"Template type: {template.__class__.__name__}")
        
        # Show what variations would be applied
        variations = VariationEngine.get_random_variations(2)
        
        print(f"\n=== SELECTED VARIATIONS ===\n")
        for i, variation in enumerate(variations, 1):
            print(f"Variation {i}: {variation}")
        
        # If thread analysis is enabled, show the analysis results
        if os.environ.get("ENABLE_THREAD_ANALYSIS", "").lower() == "true" and verbose:
            print(f"\n=== THREAD ANALYSIS ===\n")
            thread_analyzer = ThreadAnalyzer(reddit)
            thread_analysis = thread_analyzer.analyze_thread(submission)
            
            print("Thread Analysis Results:")
            print(f"- Comment Count: {thread_analysis.get('comment_count', 'N/A')}")
            print(f"- Thread Depth: {thread_analysis.get('thread_depth', 'N/A')}")
            print(f"- Key Topics: {', '.join(thread_analysis.get('key_topics', []))}")
            
            # Show response strategy
            strategy = ResponseStrategy()
            response_strategy = strategy.determine_strategy(thread_analysis, context)
            
            print(f"\nResponse Strategy:")
            print(f"- Type: {response_strategy.get('type', 'N/A')}")
            print(f"- Reasoning: {response_strategy.get('reasoning', 'N/A')}")
            
    except Exception as e:
        logger.error(f"Error showing context for submission {submission_id}: {str(e)}")


def view_submission_comments(submission_id, verbose=False):
    """
    View the comments on a specific submission.
    
    Args:
        submission_id (str): The Reddit ID of the submission
        verbose (bool): Whether to show detailed information
    """
    logger = logging.getLogger("CommentViewer")
    logger.info(f"Viewing comments for submission {submission_id}")
    
    try:
        # Get Reddit instance
        reddit = get_reddit_instance(BOT_USERNAME)
        print(f"Authenticated as {reddit.user.me()}")
        
        # Get the submission
        submission = reddit.submission(id=submission_id)
        
        print(f"\nPost Title: {submission.title}")
        print(f"Post Content: {submission.selftext[:200]}..." if len(submission.selftext) > 200 else submission.selftext)
        print(f"Author: {submission.author}")
        print(f"Score: {submission.score}")
        print(f"Created: {datetime.datetime.fromtimestamp(submission.created_utc)}")
        print(f"Number of Comments: {submission.num_comments}")
        
        # Get and display comments
        submission.comments.replace_more(limit=0)  # Fetch all comments
        print("\n--- Comments ---")
        
        # Determine how many comments to show
        comments_to_show = submission.comments if verbose else submission.comments[:10]
        
        for i, comment in enumerate(comments_to_show, 1):
            print(f"{i}. Author: {comment.author}")
            print(f"   Score: {comment.score}")
            print(f"   Created: {datetime.datetime.fromtimestamp(comment.created_utc)}")
            
            # Format the comment content
            if len(comment.body) > 200 and not verbose:
                comment_text = f"{comment.body[:200]}..."
            else:
                comment_text = comment.body
                
            print(f"   Comment: {comment_text}")
            print("-" * 50)
            
        if not verbose and submission.num_comments > 10:
            print(f"\nShowing 10 of {submission.num_comments} comments. Use --verbose to see all.")
        
    except Exception as e:
        logger.error(f"Error viewing comments for submission {submission_id}: {str(e)}")


def main():
    """Main entry point for Project Authentica."""
    # Parse arguments
    args = parse_arguments()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("Authentica")
    
    # Set environment variables based on arguments
    if args.dry_run:
        os.environ["DRY_RUN"] = "true"
    
    # Handle utility commands first (these don't require a full bot setup)
    if args.check_comment:
        return check_comment_status(args.check_comment, args.verbose)
    
    if args.show_context:
        return show_submission_context(args.show_context, args.verbose)
    
    if args.view_comments:
        return view_submission_comments(args.view_comments, args.verbose)
    
    # For the main bot operations (once or scheduled)
    if args.once:
        # Run once mode
        run_once(
            subreddit_name=args.subreddit,
            post_limit=args.limit,
            sort=args.sort,
            verbose=args.verbose
        )
    else:
        # Default to scheduled mode
        run_scheduled(
            subreddit_names=[args.subreddit],
            post_limit=args.limit,
            interval_minutes=args.interval,
            jitter_minutes=args.jitter,
            verbose=args.verbose
        )


if __name__ == "__main__":
    main()
