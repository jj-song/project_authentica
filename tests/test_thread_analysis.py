#!/usr/bin/env python3
"""
Tests for the thread_analysis module.
"""

import unittest
from unittest.mock import MagicMock, patch
import datetime

import praw

from src.thread_analysis.analyzer import ThreadAnalyzer


class TestThreadAnalyzer(unittest.TestCase):
    """Tests for the ThreadAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_reddit = MagicMock(spec=praw.Reddit)
        self.thread_analyzer = ThreadAnalyzer(self.mock_reddit)
    
    def test_evaluate_submission_quality(self):
        """Test that submission quality is evaluated correctly."""
        # Create a mock submission with various attributes
        mock_submission = MagicMock()
        
        # Set creation time to 3 hours ago (good age range)
        current_time = datetime.datetime.now().timestamp()
        mock_submission.created_utc = current_time - (3 * 3600)
        
        # Set other attributes
        mock_submission.num_comments = 30  # Good comment range
        mock_submission.score = 50  # Good score
        mock_submission.title = "Why is this happening?"  # Has question mark
        mock_submission.selftext = "I've been wondering about this for a while..."  # Medium length
        
        # Calculate score
        score = self.thread_analyzer.evaluate_submission_quality(mock_submission)
        
        # We expect:
        # - 30 points for good age (1-4 hours)
        # - 30 points for good comment range (5-50)
        # - 15 points for good score (20-100)
        # - 10 points for having a question
        # - 5 points for medium-length content
        # Total: 90 points
        self.assertGreaterEqual(score, 85)  # Allow for slight calculation differences
        self.assertLessEqual(score, 95)
    
    def test_evaluate_submission_quality_low(self):
        """Test that low quality submissions get low scores."""
        # Create a mock submission with poor engagement attributes
        mock_submission = MagicMock()
        
        # Set creation time to 48 hours ago (too old)
        current_time = datetime.datetime.now().timestamp()
        mock_submission.created_utc = current_time - (48 * 3600)
        
        # Set other attributes to low values
        mock_submission.num_comments = 1  # Very few comments
        mock_submission.score = 2  # Low score
        mock_submission.title = "Just a title"  # No question
        mock_submission.selftext = "Brief content"  # Short content
        
        # Calculate score
        score = self.thread_analyzer.evaluate_submission_quality(mock_submission)
        
        # We expect a low score (< 20)
        self.assertLess(score, 20)
    
    def test_rank_submissions(self):
        """Test that submissions are ranked correctly by quality."""
        # Create mock submissions
        high_quality = MagicMock()
        medium_quality = MagicMock()
        low_quality = MagicMock()
        stickied = MagicMock(stickied=True)
        distinguished = MagicMock(distinguished="moderator")
        meta_post = MagicMock(stickied=False, distinguished=None)
        meta_post.title = "Subreddit Rules Update"
        
        # Set current time
        current_time = datetime.datetime.now().timestamp()
        
        # High quality post - 3 hours old, 40 comments, 120 score
        high_quality.stickied = False
        high_quality.distinguished = None
        high_quality.created_utc = current_time - (3 * 3600)
        high_quality.num_comments = 40
        high_quality.score = 120
        high_quality.title = "Why do you think this happens?"
        high_quality.selftext = "I've been wondering about this for a long time and would appreciate your thoughts."
        
        # Medium quality post - 10 hours old, 15 comments, 25 score
        medium_quality.stickied = False
        medium_quality.distinguished = None
        medium_quality.created_utc = current_time - (10 * 3600)
        medium_quality.num_comments = 15
        medium_quality.score = 25
        medium_quality.title = "This happened to me today"
        medium_quality.selftext = "Just a short story."
        
        # Low quality post - 20 hours old, 3 comments, 5 score
        low_quality.stickied = False
        low_quality.distinguished = None
        low_quality.created_utc = current_time - (20 * 3600)
        low_quality.num_comments = 3
        low_quality.score = 5
        low_quality.title = "Title"
        low_quality.selftext = "Text"
        
        # Create submission list with mixed order
        submissions = [medium_quality, stickied, low_quality, meta_post, high_quality, distinguished]
        
        # Rank submissions
        ranked_submissions = self.thread_analyzer.rank_submissions(submissions)
        
        # Check results
        # We should only get non-stickied, non-distinguished, non-meta posts
        self.assertEqual(len(ranked_submissions), 3)
        
        # The first post should be the highest quality
        self.assertEqual(ranked_submissions[0][1], high_quality)
        
        # The last post should be the lowest quality
        self.assertEqual(ranked_submissions[-1][1], low_quality)
    
    def test_rank_submissions_empty(self):
        """Test ranking with all unsuitable submissions."""
        # Create only stickied or meta posts
        stickied1 = MagicMock(stickied=True)
        stickied2 = MagicMock(stickied=True)
        meta_post = MagicMock(stickied=False, distinguished=None)
        meta_post.title = "Announcement: New Rules"
        
        # Create submission list
        submissions = [stickied1, stickied2, meta_post]
        
        # Rank submissions
        ranked_submissions = self.thread_analyzer.rank_submissions(submissions)
        
        # Check that no submissions passed the filter
        self.assertEqual(len(ranked_submissions), 0)


if __name__ == "__main__":
    unittest.main() 