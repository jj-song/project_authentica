#!/usr/bin/env python3
"""
Context collector module for Project Authentica.
Collects and processes context information for prompt engineering.
"""

import logging
import datetime
import random
from typing import Dict, Any, Optional, List, Tuple

import praw
from praw.models import Submission, Comment, Subreddit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ContextCollector:
    """
    Collects and processes context information for prompt engineering.
    
    This class is responsible for gathering all relevant contextual information
    that can be used to enhance prompt engineering, including:
    - Subreddit-specific context (rules, culture, typical responses)
    - Thread history (existing comments, conversation flow)
    - Time-based context (time of day, day of week)
    """
    
    def __init__(self, reddit_instance: praw.Reddit):
        """
        Initialize the ContextCollector.
        
        Args:
            reddit_instance (praw.Reddit): An authenticated Reddit instance.
        """
        self.reddit = reddit_instance
        self.subreddit_cache = {}  # Cache for subreddit information
        self.comment_length_cache = {}  # Cache for comment length analysis
    
    def collect_context(self, submission: Submission, max_comments: int = 10) -> Dict[str, Any]:
        """
        Collect all relevant context for a submission.
        
        Args:
            submission (Submission): The Reddit submission to collect context for.
            max_comments (int, optional): Maximum number of comments to collect. Defaults to 10.
            
        Returns:
            Dict[str, Any]: A dictionary containing all collected context information.
        """
        logger.info(f"Collecting context for submission {submission.id} in r/{submission.subreddit.display_name}")
        
        # Initialize context dictionary
        context = {
            "submission": self._get_submission_context(submission),
            "subreddit": self._get_subreddit_context(submission.subreddit),
            "comments": self._get_comments_context(submission, max_comments),
            "temporal": self._get_temporal_context(),
        }
        
        # Add comment length statistics
        subreddit_name = submission.subreddit.display_name
        if subreddit_name not in self.comment_length_cache:
            self.comment_length_cache[subreddit_name] = self.analyze_subreddit_comment_lengths(subreddit_name)
        
        context["comment_length_stats"] = self.comment_length_cache[subreddit_name]
        
        return context
    
    def _get_submission_context(self, submission: Submission) -> Dict[str, Any]:
        """
        Extract context from the submission itself.
        
        Args:
            submission (Submission): The Reddit submission.
            
        Returns:
            Dict[str, Any]: Context information from the submission.
        """
        return {
            "id": submission.id,
            "title": submission.title,
            "body": submission.selftext,
            "author": str(submission.author) if submission.author else "[deleted]",
            "score": submission.score,
            "upvote_ratio": submission.upvote_ratio,
            "created_utc": submission.created_utc,
            "num_comments": submission.num_comments,
            "is_original_content": submission.is_original_content,
            "over_18": submission.over_18,
            "permalink": submission.permalink,
            "url": submission.url,
        }
    
    def _get_subreddit_context(self, subreddit: Subreddit) -> Dict[str, Any]:
        """
        Extract context from the subreddit.
        
        Args:
            subreddit (Subreddit): The Reddit subreddit.
            
        Returns:
            Dict[str, Any]: Context information from the subreddit.
        """
        # Check if we have cached information for this subreddit
        subreddit_name = subreddit.display_name
        if subreddit_name in self.subreddit_cache:
            return self.subreddit_cache[subreddit_name]
        
        # Collect subreddit information
        try:
            rules = [rule.short_name for rule in subreddit.rules]
        except Exception as e:
            logger.warning(f"Could not fetch rules for r/{subreddit_name}: {str(e)}")
            rules = []
        
        subreddit_info = {
            "name": subreddit_name,
            "title": subreddit.title,
            "description": subreddit.public_description,
            "subscribers": subreddit.subscribers,
            "created_utc": subreddit.created_utc,
            "over18": subreddit.over18,
            "rules": rules,
        }
        
        # Cache the information
        self.subreddit_cache[subreddit_name] = subreddit_info
        
        return subreddit_info
    
    def _get_comments_context(self, submission: Submission, max_comments: int) -> List[Dict[str, Any]]:
        """
        Extract context from the submission's comments.
        
        Args:
            submission (Submission): The Reddit submission.
            max_comments (int): Maximum number of comments to collect.
            
        Returns:
            List[Dict[str, Any]]: Context information from the comments.
        """
        comments_info = []
        
        # Replace MoreComments objects to get a flattened comment tree
        submission.comments.replace_more(limit=0)
        
        # Sort comments by score (highest first) and take the top max_comments
        top_comments = sorted(submission.comments, key=lambda c: c.score, reverse=True)[:max_comments]
        
        for comment in top_comments:
            comment_info = {
                "id": comment.id,
                "body": comment.body,
                "author": str(comment.author) if comment.author else "[deleted]",
                "score": comment.score,
                "created_utc": comment.created_utc,
                "is_submitter": comment.is_submitter,
            }
            comments_info.append(comment_info)
        
        return comments_info
    
    def _get_temporal_context(self) -> Dict[str, Any]:
        """
        Extract temporal context (time-based information).
        
        Returns:
            Dict[str, Any]: Temporal context information.
        """
        now = datetime.datetime.now()
        
        return {
            "timestamp": now.timestamp(),
            "iso_format": now.isoformat(),
            "day_of_week": now.strftime("%A"),
            "hour_of_day": now.hour,
            "is_weekend": now.weekday() >= 5,  # 5 = Saturday, 6 = Sunday
        }
    
    def analyze_subreddit_comment_lengths(self, subreddit_name: str, sample_size: int = 10) -> Dict[str, int]:
        """
        Analyze the typical comment lengths in a subreddit.
        
        Args:
            subreddit_name (str): Name of the subreddit to analyze
            sample_size (int): Number of comments to sample
            
        Returns:
            Dict[str, int]: Statistics about comment lengths including average and median
        """
        logger.info(f"Analyzing comment lengths in r/{subreddit_name}")
        
        subreddit = self.reddit.subreddit(subreddit_name)
        comments = []
        
        try:
            # Collect comments from hot submissions
            for submission in subreddit.hot(limit=3):
                submission.comments.replace_more(limit=0)
                for comment in submission.comments:
                    if len(comments) >= sample_size:
                        break
                    if hasattr(comment, "body") and comment.body:
                        comments.append(len(comment.body))
                if len(comments) >= sample_size:
                    break
        except Exception as e:
            logger.warning(f"Error sampling comment lengths in r/{subreddit_name}: {str(e)}")
        
        if not comments:
            logger.info(f"No comments found in r/{subreddit_name}, using default values")
            return {"min_length": 100, "avg_length": 500, "max_length": 800, "median_length": 400}
        
        # Calculate statistics
        avg_length = int(sum(comments) / len(comments))
        min_length = max(100, min(comments))  # At least 100 characters min
        max_length = min(1000, max(800, max(comments)))  # At most 1000 characters max
        median_length = sorted(comments)[len(comments) // 2]
        
        logger.info(f"Comment length analysis for r/{subreddit_name}: avg={avg_length}, min={min_length}, max={max_length}, median={median_length}")
        
        return {
            "min_length": min_length,
            "avg_length": avg_length,
            "max_length": max_length,
            "median_length": median_length
        }
    
    def analyze_comment_context(self, submission: Submission, comment: Comment) -> Dict[str, Any]:
        """
        Analyze the context of a comment in relation to the original post.
        
        Args:
            submission (Submission): The original submission
            comment (Comment): The comment being replied to
            
        Returns:
            Dict[str, Any]: Analysis of the comment's relationship to the original post
        """
        # Determine if this is a top-level comment or a nested reply
        is_top_level = comment.parent_id.startswith('t3_')  # t3_ prefix indicates parent is a submission
        
        # Get comment depth
        depth = 0
        if hasattr(comment, "depth"):
            depth = comment.depth
        
        # Analyze if the comment directly addresses the original post
        addresses_original_content = False
        if submission.selftext:
            # Simple heuristic - check if any 5+ character sequence from the original post appears in the comment
            for i in range(len(submission.selftext) - 5):
                if submission.selftext[i:i+5] in comment.body and len(submission.selftext[i:i+5].strip()) >= 5:
                    addresses_original_content = True
                    break
        
        return {
            "is_top_level": is_top_level,
            "depth": depth,
            "addresses_original_content": addresses_original_content,
            "is_op": comment.is_submitter
        }


if __name__ == "__main__":
    # Example usage
    import os
    from src.config import get_reddit_instance
    
    # Get Reddit instance
    reddit = get_reddit_instance("my_first_bot")
    
    # Create context collector
    collector = ContextCollector(reddit)
    
    # Get a submission
    submission = reddit.submission(id="1lu5snp")  # Replace with a real submission ID
    
    # Collect context
    context = collector.collect_context(submission)
    
    # Print the context
    import json
    print(json.dumps(context, indent=2))
