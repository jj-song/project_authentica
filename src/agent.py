#!/usr/bin/env python3
"""
Agent module for Project Authentica.
Defines the KarmaAgent class that manages Reddit interactions.
"""

import logging
import sqlite3
import datetime
import random
from typing import Optional, Dict, Any, Union, List, Tuple

import praw
from praw.exceptions import PRAWException, APIException, ClientException
from praw.models import Submission, Comment

from src.llm_handler import generate_comment, generate_comment_from_submission


class KarmaAgent:
    """
    KarmaAgent is responsible for scanning subreddits, identifying relevant posts,
    and posting AI-generated comments to build karma.
    
    The agent interacts with Reddit via PRAW and logs all actions to a SQLite database.
    """
    
    def __init__(self, reddit_instance: praw.Reddit, db_connection: sqlite3.Connection):
        """
        Initialize a new KarmaAgent.
        
        Args:
            reddit_instance (praw.Reddit): An authenticated Reddit instance.
            db_connection (sqlite3.Connection): An open connection to the SQLite database.
        """
        self.reddit = reddit_instance
        self.db = db_connection
        self.username = str(self.reddit.user.me())
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"KarmaAgent-{self.username}")
        
        self.logger.info(f"KarmaAgent initialized for user: {self.username}")
    
    def scan_and_comment(self, subreddit_name: str, post_limit: int = 10, sort: str = 'hot') -> None:
        """
        Scan a subreddit for posts, identify relevant ones, and post AI-generated comments.
        
        This is the main workflow method that orchestrates the agent's activity:
        1. Log the start of the scan action
        2. Fetch submissions from the subreddit based on sort type
        3. For each submission, check if it's relevant and if we've already commented
        4. Generate and post a comment on relevant submissions
        5. Log the results of each action
        
        Args:
            subreddit_name (str): Name of the subreddit to scan (without the 'r/' prefix)
            post_limit (int, optional): Maximum number of posts to scan. Defaults to 10.
            sort (str, optional): Sort method for posts ('hot', 'new', 'top', 'rising'). Defaults to 'hot'.
        """
        # Log the start of the scan action
        self._log_action(
            action_type="SCAN_START",
            target_id=subreddit_name,
            status="INFO",
            details=f"Starting scan of r/{subreddit_name} with limit {post_limit}, sort: {sort}"
        )
        
        try:
            # Get the subreddit
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Fetch submissions based on sort type
            if sort == 'hot':
                submissions = list(subreddit.hot(limit=post_limit))
            elif sort == 'new':
                submissions = list(subreddit.new(limit=post_limit))
            elif sort == 'top':
                submissions = list(subreddit.top(limit=post_limit))
            elif sort == 'rising':
                submissions = list(subreddit.rising(limit=post_limit))
            else:
                # Default to hot if an invalid sort is provided
                submissions = list(subreddit.hot(limit=post_limit))
                sort = 'hot'
            
            self.logger.info(f"Fetched {len(submissions)} {sort} submissions from r/{subreddit_name}")
            
            # Log the completion of the fetch
            self._log_action(
                action_type="FETCH_POSTS",
                target_id=subreddit_name,
                status="SUCCESS",
                details=f"Fetched {len(submissions)} {sort} posts"
            )
            
            # Process each submission
            for submission in submissions:
                self._process_submission(submission, subreddit_name)
                
        except PRAWException as e:
            self.logger.error(f"PRAW error during scan of r/{subreddit_name}: {str(e)}")
            self._log_action(
                action_type="SCAN_ERROR",
                target_id=subreddit_name,
                status="FAILURE",
                details=f"PRAW error: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error during scan of r/{subreddit_name}: {str(e)}")
            self._log_action(
                action_type="SCAN_ERROR",
                target_id=subreddit_name,
                status="FAILURE",
                details=f"Unexpected error: {str(e)}"
            )
    
    def _process_submission(self, submission: praw.models.Submission, subreddit_name: str) -> None:
        """
        Process a single submission: check if relevant, generate and post a comment if appropriate.
        
        Args:
            submission (praw.models.Submission): The Reddit submission to process
            subreddit_name (str): Name of the subreddit (for logging purposes)
        """
        # Check if we've already commented on this submission
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT * FROM actions_log WHERE bot_username = ? AND action_type = ? AND target_id = ? AND status = ?",
            (self.username, "COMMENT", submission.id, "SUCCESS")
        )
        if cursor.fetchone():
            self.logger.info(f"Already commented on submission {submission.id}, skipping")
            return
        
        # Check if the post is relevant
        if not self._is_post_relevant(submission):
            self.logger.info(f"Submission {submission.id} deemed not relevant, skipping")
            self._log_action(
                action_type="SKIP_POST",
                target_id=submission.id,
                status="INFO",
                details="Post deemed not relevant"
            )
            return
        
        # Try to reply to a comment instead of the submission
        try:
            # First try to find a suitable comment to reply to
            if self._try_reply_to_comment(submission, subreddit_name):
                return
            
            # If no suitable comment found or if reply failed, fall back to replying to the submission
            self.logger.info(f"No suitable comment found, replying to submission {submission.id}")
            
            # Use the new context-aware comment generation
            comment_text = generate_comment_from_submission(submission, self.reddit)
            
            # Post the comment
            self.logger.info(f"Attempting to comment on submission {submission.id}")
            comment = submission.reply(comment_text)
            
            # Log the successful comment
            self.logger.info(f"Successfully commented on submission {submission.id}, comment ID: {comment.id}")
            self._log_action(
                action_type="COMMENT",
                target_id=submission.id,
                status="SUCCESS",
                details=f"Comment posted with ID {comment.id}"
            )
            
            # Create a record in comment_performance table
            current_time = datetime.datetime.now().isoformat()
            cursor.execute(
                """
                INSERT INTO comment_performance 
                (comment_id, submission_id, subreddit, initial_score, current_score, last_checked) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (comment.id, submission.id, subreddit_name, 1, 1, current_time)
            )
            self.db.commit()
            
        except (PRAWException, APIException, ClientException) as e:
            self.logger.error(f"Error posting comment to {submission.id}: {str(e)}")
            self._log_action(
                action_type="COMMENT",
                target_id=submission.id,
                status="FAILURE",
                details=f"PRAW error: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Unexpected error posting comment to {submission.id}: {str(e)}")
            self._log_action(
                action_type="COMMENT",
                target_id=submission.id,
                status="FAILURE",
                details=f"Unexpected error: {str(e)}"
            )
    
    def _try_reply_to_comment(self, submission: Submission, subreddit_name: str) -> bool:
        """
        Try to reply to an existing comment instead of the submission.
        
        Args:
            submission (Submission): The Reddit submission
            subreddit_name (str): Name of the subreddit (for logging purposes)
            
        Returns:
            bool: True if successfully replied to a comment, False otherwise
        """
        try:
            # Replace MoreComments objects to get a flattened comment tree
            submission.comments.replace_more(limit=0)
            
            # Filter for comments that:
            # 1. Have a positive score
            # 2. Are not from the bot itself
            # 3. Have some substance (not too short)
            eligible_comments = [
                comment for comment in submission.comments
                if (comment.score > 0 and 
                    str(comment.author) != self.username and
                    len(comment.body) >= 20)
            ]
            
            if not eligible_comments:
                self.logger.info(f"No eligible comments found in submission {submission.id}")
                return False
            
            # Sort by score and select a comment from the top 3 (if available)
            eligible_comments.sort(key=lambda c: c.score, reverse=True)
            top_comments = eligible_comments[:min(3, len(eligible_comments))]
            selected_comment = random.choice(top_comments)
            
            # Generate a reply using context-aware LLM handler
            comment_text = generate_comment_from_submission(submission, self.reddit, comment_to_reply=selected_comment)
            
            # Post the reply
            self.logger.info(f"Attempting to reply to comment {selected_comment.id} in submission {submission.id}")
            reply = selected_comment.reply(comment_text)
            
            # Log the successful reply
            self.logger.info(f"Successfully replied to comment {selected_comment.id}, reply ID: {reply.id}")
            self._log_action(
                action_type="COMMENT_REPLY",
                target_id=selected_comment.id,
                status="SUCCESS",
                details=f"Reply posted with ID {reply.id} on submission {submission.id}"
            )
            
            # Create a record in comment_performance table
            current_time = datetime.datetime.now().isoformat()
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO comment_performance 
                (comment_id, submission_id, subreddit, initial_score, current_score, last_checked) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (reply.id, submission.id, subreddit_name, 1, 1, current_time)
            )
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error trying to reply to a comment in submission {submission.id}: {str(e)}")
            return False
    
    def _is_post_relevant(self, submission: praw.models.Submission) -> bool:
        """
        Determine if a post is relevant for commenting.
        
        Args:
            submission (praw.models.Submission): The Reddit submission to evaluate
            
        Returns:
            bool: True if the post is relevant, False otherwise
        """
        # Skip stickied posts (like daily threads)
        if submission.stickied:
            self.logger.info(f"Skipping stickied post {submission.id}: {submission.title}")
            return False
        
        # Skip posts with "daily" or "thread" in the title (common for recurring threads)
        title_lower = submission.title.lower()
        if ("daily" in title_lower and "thread" in title_lower) or "daily help thread" in title_lower:
            self.logger.info(f"Skipping daily thread post {submission.id}: {submission.title}")
            return False
        
        # Skip posts with very low scores
        if submission.score < 1:
            self.logger.info(f"Skipping low-score post {submission.id}: score {submission.score}")
            return False
        
        # Skip posts with no comments (prefer posts with some engagement)
        if submission.num_comments == 0:
            self.logger.info(f"Skipping post with no comments {submission.id}")
            return False
        
        # TODO: Add more relevance criteria as needed
        
        return True
    
    def _log_action(self, action_type: str, target_id: str, status: str, details: Optional[str] = None) -> None:
        """
        Log an action to the actions_log table in the database.
        
        Args:
            action_type (str): Type of action (e.g., "SCAN_START", "COMMENT", "SKIP_POST")
            target_id (str): ID of the target (submission ID, subreddit name, etc.)
            status (str): Status of the action (e.g., "SUCCESS", "FAILURE", "INFO")
            details (Optional[str], optional): Additional details about the action. Defaults to None.
        """
        try:
            timestamp = datetime.datetime.now().isoformat()
            cursor = self.db.cursor()
            cursor.execute(
                """
                INSERT INTO actions_log 
                (bot_username, action_type, target_id, status, details, timestamp) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (self.username, action_type, target_id, status, details, timestamp)
            )
            self.db.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Database error when logging action: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error when logging action: {str(e)}")

    def record_comment(self, comment_id: str, submission_id: str, reply_to_id: Optional[str] = None) -> None:
        """
        Record a comment in the database after successful posting.
        
        Args:
            comment_id (str): ID of the posted comment
            submission_id (str): ID of the submission the comment was posted on
            reply_to_id (Optional[str], optional): ID of the comment being replied to, if any. Defaults to None.
        """
        try:
            # Log the successful comment action
            self._log_action(
                action_type="COMMENT_RECORDED",
                target_id=comment_id,
                status="SUCCESS",
                details=f"Comment posted on submission {submission_id}" + (f", reply to {reply_to_id}" if reply_to_id else "")
            )
            
            # Create a record in comment_performance table
            current_time = datetime.datetime.now().isoformat()
            cursor = self.db.cursor()
            
            # Get the subreddit name from the submission ID if needed
            subreddit_name = "unknown"  # Default fallback
            try:
                submission = self.reddit.submission(id=submission_id)
                subreddit_name = str(submission.subreddit)
            except Exception as e:
                self.logger.error(f"Error getting subreddit name for submission {submission_id}: {str(e)}")
            
            # Insert into comment_performance table
            cursor.execute(
                """
                INSERT INTO comment_performance 
                (comment_id, submission_id, subreddit, initial_score, current_score, last_checked) 
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (comment_id, submission_id, subreddit_name, 1, 1, current_time)
            )
            self.db.commit()
            self.logger.info(f"Recorded comment {comment_id} in database")
        except Exception as e:
            self.logger.error(f"Error recording comment {comment_id}: {str(e)}")

    def reply_to_comment(self, comment: Comment, comment_text: str) -> Optional[Comment]:
        """
        Reply to a specific comment.
        
        Args:
            comment (Comment): The comment to reply to
            comment_text (str): The text content for the reply
            
        Returns:
            Optional[Comment]: The posted comment object if successful, None otherwise
        """
        try:
            self.logger.info(f"Attempting to reply to comment {comment.id}")
            reply = comment.reply(comment_text)
            
            # Log the successful reply
            self.logger.info(f"Successfully replied to comment {comment.id}, reply ID: {reply.id}")
            self._log_action(
                action_type="COMMENT_REPLY",
                target_id=comment.id,
                status="SUCCESS",
                details=f"Reply posted with ID {reply.id} on submission {comment.submission.id}"
            )
            
            # Record the comment
            self.record_comment(reply.id, comment.submission.id, comment.id)
            
            return reply
        except Exception as e:
            self.logger.error(f"Error replying to comment {comment.id}: {str(e)}")
            self._log_action(
                action_type="COMMENT_REPLY",
                target_id=comment.id,
                status="FAILURE",
                details=f"Error: {str(e)}"
            )
            return None

    def reply_to_submission(self, submission: Submission, comment_text: str) -> Optional[Comment]:
        """
        Reply to a submission with a comment.
        
        Args:
            submission (Submission): The submission to reply to
            comment_text (str): The text content for the comment
            
        Returns:
            Optional[Comment]: The posted comment object if successful, None otherwise
        """
        try:
            self.logger.info(f"Attempting to comment on submission {submission.id}")
            comment = submission.reply(comment_text)
            
            # Log the successful comment
            self.logger.info(f"Successfully commented on submission {submission.id}, comment ID: {comment.id}")
            self._log_action(
                action_type="COMMENT",
                target_id=submission.id,
                status="SUCCESS",
                details=f"Comment posted with ID {comment.id}"
            )
            
            # Record the comment
            self.record_comment(comment.id, submission.id)
            
            return comment
        except Exception as e:
            self.logger.error(f"Error commenting on submission {submission.id}: {str(e)}")
            self._log_action(
                action_type="COMMENT",
                target_id=submission.id,
                status="FAILURE",
                details=f"Error: {str(e)}"
            )
            return None


if __name__ == "__main__":
    # Example usage (for demonstration purposes only)
    import sys
    from src.database import get_db_connection
    from src.config import get_reddit_instance
    
    if len(sys.argv) > 2:
        bot_username = sys.argv[1]
        subreddit_name = sys.argv[2]
        post_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        
        try:
            # Get Reddit instance and DB connection
            reddit = get_reddit_instance(bot_username)
            db_conn = get_db_connection()
            
            # Create and run agent
            agent = KarmaAgent(reddit, db_conn)
            agent.scan_and_comment(subreddit_name, post_limit)
            
            print(f"Agent completed scan of r/{subreddit_name}")
            
            # Close DB connection
            db_conn.close()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Usage: python agent.py <bot_username> <subreddit_name> [post_limit]") 
