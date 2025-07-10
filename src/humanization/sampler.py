#!/usr/bin/env python3
"""
Comment Sampler Module for Project Authentica.
Collects and manages representative comment samples from subreddits.
"""

import logging
import random
import sqlite3
import time
from typing import Dict, List, Any, Optional

import praw
from praw.models import Submission, Subreddit

from src.humanization.analyzer import CommentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CommentSampler:
    """
    Collects and manages representative comment samples from subreddits.
    
    This class provides methods for:
    1. Collecting sample comments from target subreddits
    2. Storing samples in a database
    3. Retrieving relevant samples based on context
    4. Providing representative examples for prompt enhancement
    """
    
    def __init__(self, reddit_instance: praw.Reddit, db_connection: sqlite3.Connection):
        """
        Initialize the CommentSampler.
        
        Args:
            reddit_instance (praw.Reddit): An authenticated Reddit instance
            db_connection (sqlite3.Connection): Database connection for storing samples
        """
        self.reddit = reddit_instance
        self.db = db_connection
        self.analyzer = CommentAnalyzer(reddit_instance)
        
        # Ensure the database table exists
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Initialize the database tables for storing comment samples."""
        cursor = self.db.cursor()
        
        # Create table for comment samples
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comment_samples (
            id TEXT PRIMARY KEY,
            subreddit TEXT NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_utc REAL NOT NULL,
            submission_id TEXT NOT NULL,
            is_top_level INTEGER NOT NULL,
            collected_at REAL NOT NULL
        )
        ''')
        
        # Create table for subreddit profiles
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subreddit_profiles (
            subreddit TEXT PRIMARY KEY,
            profile TEXT NOT NULL,  -- JSON string of the profile
            updated_at REAL NOT NULL
        )
        ''')
        
        self.db.commit()
    
    def collect_samples(self, subreddit_name: str, count: int = 100, force_update: bool = False) -> List[Dict[str, Any]]:
        """
        Collect sample comments from a subreddit and store them in the database.
        
        Args:
            subreddit_name (str): Name of the subreddit to sample
            count (int): Number of comments to collect
            force_update (bool): Whether to force an update even if recent samples exist
            
        Returns:
            List[Dict[str, Any]]: The collected comment samples
        """
        # Check if we have recent samples (less than 24 hours old)
        if not force_update:
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM comment_samples WHERE subreddit = ? AND collected_at > ?",
                (subreddit_name, time.time() - 86400)  # 24 hours in seconds
            )
            recent_count = cursor.fetchone()[0]
            
            if recent_count >= count:
                logger.info(f"Using {recent_count} existing recent samples for r/{subreddit_name}")
                return self._get_stored_samples(subreddit_name, count)
        
        # Collect new samples
        logger.info(f"Collecting {count} new samples from r/{subreddit_name}")
        self.analyzer.sample_size = count
        comments = self.analyzer.collect_comments(subreddit_name)
        
        # Store in database
        self._store_samples(comments)
        
        return comments
    
    def _store_samples(self, comments: List[Dict[str, Any]]) -> None:
        """
        Store comment samples in the database.
        
        Args:
            comments (List[Dict[str, Any]]): List of comment data dictionaries
        """
        cursor = self.db.cursor()
        current_time = time.time()
        
        for comment in comments:
            cursor.execute(
                """
                INSERT OR REPLACE INTO comment_samples 
                (id, subreddit, author, body, score, created_utc, submission_id, is_top_level, collected_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    comment['id'],
                    comment.get('subreddit', 'unknown'),
                    comment['author'],
                    comment['body'],
                    comment['score'],
                    comment['created_utc'],
                    comment['submission_id'],
                    1 if comment['is_top_level'] else 0,
                    current_time
                )
            )
        
        self.db.commit()
        logger.info(f"Stored {len(comments)} comment samples in database")
    
    def _get_stored_samples(self, subreddit_name: str, count: int) -> List[Dict[str, Any]]:
        """
        Retrieve stored comment samples from the database.
        
        Args:
            subreddit_name (str): Name of the subreddit
            count (int): Maximum number of samples to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of comment data dictionaries
        """
        cursor = self.db.cursor()
        cursor.execute(
            """
            SELECT id, author, body, score, created_utc, submission_id, is_top_level
            FROM comment_samples
            WHERE subreddit = ?
            ORDER BY collected_at DESC, score DESC
            LIMIT ?
            """,
            (subreddit_name, count)
        )
        
        comments = []
        for row in cursor.fetchall():
            comments.append({
                'id': row[0],
                'author': row[1],
                'body': row[2],
                'score': row[3],
                'created_utc': row[4],
                'submission_id': row[5],
                'is_top_level': bool(row[6]),
                'subreddit': subreddit_name
            })
        
        return comments
    
    def get_representative_samples(self, subreddit_name: str, context: Dict[str, Any], count: int = 5) -> List[Dict[str, Any]]:
        """
        Get representative comments that are similar to the current context.
        
        Args:
            subreddit_name (str): Name of the subreddit
            context (Dict[str, Any]): Current context information
            count (int): Number of samples to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of representative comment samples
        """
        # Ensure we have samples for this subreddit
        all_samples = self.collect_samples(subreddit_name)
        if not all_samples:
            logger.warning(f"No samples available for r/{subreddit_name}")
            return []
        
        # Filter for comments that match the context
        is_reply = 'comment_to_reply' in context
        filtered_samples = [
            comment for comment in all_samples
            if comment['is_top_level'] != is_reply  # Match reply vs direct comment
        ]
        
        if not filtered_samples:
            filtered_samples = all_samples  # Fallback to all samples
        
        # Sort by score and select top samples
        filtered_samples.sort(key=lambda c: c['score'], reverse=True)
        top_samples = filtered_samples[:min(15, len(filtered_samples))]
        
        # Select a diverse set from the top samples
        if len(top_samples) <= count:
            return top_samples
        else:
            # Select some high-scoring and some random for diversity
            high_scoring = top_samples[:count//2]
            random_selection = random.sample(top_samples[count//2:], count - len(high_scoring))
            return high_scoring + random_selection
    
    def update_subreddit_profile(self, subreddit_name: str) -> Dict[str, Any]:
        """
        Update the stored profile for a subreddit.
        
        Args:
            subreddit_name (str): Name of the subreddit
            
        Returns:
            Dict[str, Any]: The updated subreddit profile
        """
        # Get samples and analyze them
        comments = self.collect_samples(subreddit_name, force_update=True)
        profile = self.analyzer.analyze_comments(comments)
        
        # Add subreddit metadata
        subreddit = self.reddit.subreddit(subreddit_name)
        profile['subreddit'] = {
            'name': subreddit_name,
            'display_name': subreddit.display_name,
            'subscribers': subreddit.subscribers,
            'description': subreddit.public_description or subreddit.description
        }
        
        # Store the profile
        import json
        cursor = self.db.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO subreddit_profiles
            (subreddit, profile, updated_at)
            VALUES (?, ?, ?)
            """,
            (subreddit_name, json.dumps(profile), time.time())
        )
        self.db.commit()
        
        return profile
    
    def get_subreddit_profile(self, subreddit_name: str, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """
        Get the stored profile for a subreddit, updating if necessary.
        
        Args:
            subreddit_name (str): Name of the subreddit
            max_age_hours (int): Maximum age of the profile in hours before updating
            
        Returns:
            Optional[Dict[str, Any]]: The subreddit profile, or None if unavailable
        """
        cursor = self.db.cursor()
        cursor.execute(
            "SELECT profile, updated_at FROM subreddit_profiles WHERE subreddit = ?",
            (subreddit_name,)
        )
        row = cursor.fetchone()
        
        if row and (time.time() - row[1]) < (max_age_hours * 3600):
            # Profile exists and is recent enough
            import json
            return json.loads(row[0])
        else:
            # Profile doesn't exist or is too old, update it
            return self.update_subreddit_profile(subreddit_name)


if __name__ == "__main__":
    # Example usage
    import os
    from src.config import get_reddit_instance
    from src.database import get_db_connection
    
    reddit = get_reddit_instance(os.getenv("BOT_USERNAME", "my_first_bot"))
    db_conn = get_db_connection()
    
    sampler = CommentSampler(reddit, db_conn)
    
    subreddit_name = "formula1"
    samples = sampler.collect_samples(subreddit_name, count=20)
    
    print(f"=== Comment Samples for r/{subreddit_name} ===")
    for i, sample in enumerate(samples[:3], 1):
        print(f"\nSample {i}:")
        print(f"Author: {sample['author']}")
        print(f"Score: {sample['score']}")
        print(f"Content: {sample['body'][:100]}..." if len(sample['body']) > 100 else f"Content: {sample['body']}")
    
    # Clean up
    db_conn.close() 