#!/usr/bin/env python3
"""
Thread Analyzer module for Project Authentica.
Provides tools for analyzing Reddit threads and extracting insights.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict
import re
import praw
from praw.models import Submission, Comment, MoreComments
import datetime

from src.thread_analysis.conversation import ConversationFlow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ThreadAnalyzer:
    """
    Analyzes Reddit threads to extract insights and patterns.
    
    This class provides methods for:
    1. Deep thread traversal (beyond the initial comment layer)
    2. Identifying key discussion topics and themes
    3. Analyzing sentiment and engagement patterns
    4. Detecting conversation dynamics and flow
    """
    
    def __init__(self, reddit_instance: praw.Reddit):
        """
        Initialize the ThreadAnalyzer.
        
        Args:
            reddit_instance (praw.Reddit): An authenticated Reddit instance.
        """
        self.reddit = reddit_instance
        self.conversation_flow = ConversationFlow()
    
    def analyze_thread(self, submission: Submission, max_depth: int = 5, max_comments: int = 100) -> Dict[str, Any]:
        """
        Perform a comprehensive analysis of a Reddit thread.
        
        Args:
            submission (Submission): The Reddit submission to analyze.
            max_depth (int): Maximum depth of comment traversal.
            max_comments (int): Maximum number of comments to analyze.
            
        Returns:
            Dict[str, Any]: Analysis results including key topics, sentiment, and conversation flow.
        """
        logger.info(f"Analyzing thread: {submission.title} (ID: {submission.id})")
        
        # Initialize analysis results
        analysis = {
            "submission_id": submission.id,
            "title": submission.title,
            "key_topics": [],
            "sentiment": {},
            "conversation_flow": {},
            "user_engagement": {},
            "comment_count": 0,
            "thread_depth": 0,
            "top_contributors": [],
            "comment_forest": {},
        }
        
        # Extract all comments with full thread structure
        comment_forest = self._extract_comment_forest(submission, max_depth, max_comments)
        analysis["comment_forest"] = comment_forest
        analysis["comment_count"] = self._count_comments(comment_forest)
        analysis["thread_depth"] = self._calculate_max_depth(comment_forest)
        
        # Extract key topics from title and comments
        analysis["key_topics"] = self._extract_key_topics(submission, comment_forest)
        
        # Analyze sentiment across the thread
        analysis["sentiment"] = self._analyze_sentiment(comment_forest)
        
        # Analyze conversation flow
        analysis["conversation_flow"] = self.conversation_flow.analyze(comment_forest)
        
        # Analyze user engagement
        analysis["user_engagement"] = self._analyze_user_engagement(comment_forest)
        
        # Identify top contributors
        analysis["top_contributors"] = self._identify_top_contributors(comment_forest)
        
        logger.info(f"Thread analysis complete for {submission.id}: {len(analysis['key_topics'])} key topics identified")
        return analysis
    
    def _extract_comment_forest(self, submission: Submission, max_depth: int, max_comments: int) -> Dict[str, Any]:
        """
        Extract the full comment forest with hierarchical structure.
        
        Args:
            submission (Submission): The Reddit submission.
            max_depth (int): Maximum depth to traverse.
            max_comments (int): Maximum comments to extract.
            
        Returns:
            Dict[str, Any]: Hierarchical comment structure.
        """
        logger.info(f"Extracting comment forest for submission {submission.id}")
        
        # Replace all MoreComments objects to get the full thread
        submission.comments.replace_more(limit=None)
        
        # Build the comment forest
        forest = {}
        comment_count = 0
        
        for top_level_comment in submission.comments:
            if comment_count >= max_comments:
                break
                
            forest[top_level_comment.id] = self._process_comment(top_level_comment, 1, max_depth, max_comments - comment_count)
            comment_count += self._count_comments({top_level_comment.id: forest[top_level_comment.id]})
        
        logger.info(f"Extracted {comment_count} comments from submission {submission.id}")
        return forest
    
    def _process_comment(self, comment: Comment, current_depth: int, max_depth: int, max_comments: int) -> Dict[str, Any]:
        """
        Process a comment and its replies recursively.
        
        Args:
            comment (Comment): The comment to process.
            current_depth (int): Current depth in the comment tree.
            max_depth (int): Maximum depth to traverse.
            max_comments (int): Maximum comments to process.
            
        Returns:
            Dict[str, Any]: Processed comment with its replies.
        """
        # Extract basic comment information
        comment_data = {
            "id": comment.id,
            "author": str(comment.author) if comment.author else "[deleted]",
            "body": comment.body,
            "score": comment.score,
            "created_utc": comment.created_utc,
            "edited": bool(comment.edited),
            "is_submitter": comment.is_submitter,
            "depth": current_depth,
            "replies": {},
        }
        
        # Stop recursion if we've reached max depth or max comments
        if current_depth >= max_depth or max_comments <= 0:
            return comment_data
        
        # Process replies
        comment_count = 0
        for reply in comment.replies:
            if comment_count >= max_comments:
                break
                
            comment_data["replies"][reply.id] = self._process_comment(
                reply, current_depth + 1, max_depth, max_comments - comment_count
            )
            comment_count += 1 + self._count_comments({reply.id: comment_data["replies"][reply.id]})
        
        return comment_data
    
    def _count_comments(self, comment_forest: Dict[str, Any]) -> int:
        """
        Count the total number of comments in a comment forest.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest to count.
            
        Returns:
            int: Total number of comments.
        """
        count = len(comment_forest)
        
        for comment_id, comment_data in comment_forest.items():
            if "replies" in comment_data:
                count += self._count_comments(comment_data["replies"])
        
        return count
    
    def _calculate_max_depth(self, comment_forest: Dict[str, Any]) -> int:
        """
        Calculate the maximum depth of the comment forest.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest to analyze.
            
        Returns:
            int: Maximum depth of the comment tree.
        """
        max_depth = 0
        
        for comment_id, comment_data in comment_forest.items():
            if "depth" in comment_data:
                max_depth = max(max_depth, comment_data["depth"])
            
            if "replies" in comment_data and comment_data["replies"]:
                max_depth = max(max_depth, self._calculate_max_depth(comment_data["replies"]))
        
        return max_depth
    
    def _extract_key_topics(self, submission: Submission, comment_forest: Dict[str, Any]) -> List[str]:
        """
        Extract key topics from the submission and comments.
        
        Args:
            submission (Submission): The Reddit submission.
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            List[str]: List of key topics.
        """
        # This is a simplified implementation
        # In a production system, you would use NLP techniques like topic modeling
        
        # Combine title and selftext
        text = submission.title + " " + submission.selftext
        
        # Extract potential topics (simple keyword extraction)
        potential_topics = set()
        
        # Add words from title that might be topics (simple heuristic)
        words = re.findall(r'\b[A-Z][a-z]{2,}\b', submission.title)
        potential_topics.update(words)
        
        # Extract topics from comments (simplified)
        self._extract_topics_from_comments(comment_forest, potential_topics)
        
        # Return the top topics (limited to 10)
        return list(potential_topics)[:10]
    
    def _extract_topics_from_comments(self, comment_forest: Dict[str, Any], topics: Set[str]) -> None:
        """
        Extract topics from comments recursively.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            topics (Set[str]): Set to update with extracted topics.
        """
        for comment_id, comment_data in comment_forest.items():
            if "body" in comment_data:
                # Extract capitalized words that might be topics
                words = re.findall(r'\b[A-Z][a-z]{2,}\b', comment_data["body"])
                topics.update(words)
            
            if "replies" in comment_data:
                self._extract_topics_from_comments(comment_data["replies"], topics)
    
    def _analyze_sentiment(self, comment_forest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment across the thread.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            Dict[str, Any]: Sentiment analysis results.
        """
        # This is a simplified implementation
        # In a production system, you would use NLP techniques for sentiment analysis
        
        sentiment = {
            "overall": "neutral",
            "distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            }
        }
        
        # Process comments for sentiment
        self._process_comments_for_sentiment(comment_forest, sentiment["distribution"])
        
        # Determine overall sentiment
        total = sum(sentiment["distribution"].values())
        if total > 0:
            if sentiment["distribution"]["positive"] > sentiment["distribution"]["negative"]:
                sentiment["overall"] = "positive"
            elif sentiment["distribution"]["negative"] > sentiment["distribution"]["positive"]:
                sentiment["overall"] = "negative"
        
        return sentiment
    
    def _process_comments_for_sentiment(self, comment_forest: Dict[str, Any], distribution: Dict[str, int]) -> None:
        """
        Process comments for sentiment analysis recursively.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            distribution (Dict[str, int]): Sentiment distribution to update.
        """
        # Simple keyword-based sentiment analysis (for demonstration)
        positive_words = {"good", "great", "excellent", "amazing", "love", "best", "awesome", "fantastic"}
        negative_words = {"bad", "terrible", "awful", "worst", "hate", "poor", "horrible", "disappointing"}
        
        for comment_id, comment_data in comment_forest.items():
            if "body" in comment_data:
                text = comment_data["body"].lower()
                
                # Count positive and negative words
                pos_count = sum(1 for word in positive_words if word in text)
                neg_count = sum(1 for word in negative_words if word in text)
                
                # Determine sentiment
                if pos_count > neg_count:
                    distribution["positive"] += 1
                elif neg_count > pos_count:
                    distribution["negative"] += 1
                else:
                    distribution["neutral"] += 1
            
            if "replies" in comment_data:
                self._process_comments_for_sentiment(comment_data["replies"], distribution)
    
    def _analyze_user_engagement(self, comment_forest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze user engagement patterns.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            Dict[str, Any]: User engagement analysis.
        """
        engagement = {
            "unique_users": set(),
            "user_comment_counts": defaultdict(int),
            "user_depth": defaultdict(list),
            "submitter_engagement": 0,
        }
        
        # Process comments for user engagement
        self._process_comments_for_engagement(comment_forest, engagement)
        
        # Convert sets to lists for JSON serialization
        engagement["unique_users"] = list(engagement["unique_users"])
        engagement["user_comment_counts"] = dict(engagement["user_comment_counts"])
        
        # Calculate average depth per user
        avg_depth = {}
        for user, depths in engagement["user_depth"].items():
            if depths:
                avg_depth[user] = sum(depths) / len(depths)
        
        engagement["avg_user_depth"] = avg_depth
        del engagement["user_depth"]  # Remove raw depth data
        
        return engagement
    
    def _process_comments_for_engagement(self, comment_forest: Dict[str, Any], engagement: Dict[str, Any]) -> None:
        """
        Process comments for user engagement analysis recursively.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            engagement (Dict[str, Any]): Engagement data to update.
        """
        for comment_id, comment_data in comment_forest.items():
            if "author" in comment_data and comment_data["author"] != "[deleted]":
                author = comment_data["author"]
                
                # Update unique users
                engagement["unique_users"].add(author)
                
                # Update comment counts
                engagement["user_comment_counts"][author] += 1
                
                # Update depth information
                if "depth" in comment_data:
                    engagement["user_depth"][author].append(comment_data["depth"])
                
                # Track submitter engagement
                if "is_submitter" in comment_data and comment_data["is_submitter"]:
                    engagement["submitter_engagement"] += 1
            
            if "replies" in comment_data:
                self._process_comments_for_engagement(comment_data["replies"], engagement)
    
    def _identify_top_contributors(self, comment_forest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify top contributors based on comment count and scores.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            List[Dict[str, Any]]: List of top contributors with their stats.
        """
        # Track user stats
        user_stats = defaultdict(lambda: {"comment_count": 0, "total_score": 0, "avg_score": 0})
        
        # Process comments to collect user stats
        self._process_comments_for_contributors(comment_forest, user_stats)
        
        # Calculate average scores
        for user, stats in user_stats.items():
            if stats["comment_count"] > 0:
                stats["avg_score"] = stats["total_score"] / stats["comment_count"]
        
        # Convert to list and sort by comment count (primary) and average score (secondary)
        contributors = [{"username": user, **stats} for user, stats in user_stats.items()]
        contributors.sort(key=lambda x: (x["comment_count"], x["avg_score"]), reverse=True)
        
        # Return top 10 contributors
        return contributors[:10]
    
    def _process_comments_for_contributors(self, comment_forest: Dict[str, Any], user_stats: Dict[str, Dict[str, Any]]) -> None:
        """
        Process comments to gather contributor statistics recursively.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest to process.
            user_stats (Dict[str, Dict[str, Any]]): User statistics to update.
        """
        for comment_id, comment_data in comment_forest.items():
            author = comment_data.get("author")
            if author and author != "[deleted]":
                if author not in user_stats:
                    user_stats[author] = {
                        "comment_count": 0,
                        "total_score": 0,
                        "avg_score": 0,
                        "highest_score": 0,
                    }
                
                score = comment_data.get("score", 0)
                user_stats[author]["comment_count"] += 1
                user_stats[author]["total_score"] += score
                user_stats[author]["avg_score"] = user_stats[author]["total_score"] / user_stats[author]["comment_count"]
                user_stats[author]["highest_score"] = max(user_stats[author]["highest_score"], score)
            
            if "replies" in comment_data:
                self._process_comments_for_contributors(comment_data["replies"], user_stats)
    
    def evaluate_submission_quality(self, submission: Submission) -> float:
        """
        Evaluate the quality of a submission for engagement.
        
        Args:
            submission (Submission): The submission to evaluate
            
        Returns:
            float: Quality score between 0 and 100
        """
        score = 0
        
        # Age factor: prefer posts between 1-12 hours old (fresher but with some traction)
        post_age_hours = (datetime.datetime.now().timestamp() - submission.created_utc) / 3600
        if 1 <= post_age_hours <= 4:
            score += 30  # Optimal age range
        elif 4 < post_age_hours <= 12:
            score += 20  # Good age range
        elif 12 < post_age_hours <= 24:
            score += 10  # Acceptable age range
        
        # Comment count factor: prefer posts with good discussion but not overwhelmed
        if 5 <= submission.num_comments <= 50:
            score += 30  # Optimal comment range
        elif 50 < submission.num_comments <= 200:
            score += 20  # Good comment range
        elif submission.num_comments > 200:
            score += 10  # Lots of comments, harder to stand out
        elif submission.num_comments > 0:
            score += 5   # At least some comments
        
        # Score factor: prefer posts with positive engagement
        if submission.score >= 100:
            score += 20  # Well-received post
        elif submission.score >= 20:
            score += 15  # Positively received
        elif submission.score >= 5:
            score += 10  # Some positive reception
        elif submission.score >= 1:
            score += 5   # At least not downvoted
        
        # Question factor: posts with questions are good for engagement
        if "?" in submission.title or "?" in submission.selftext:
            score += 10
        
        # Content factor: prefer posts with substantial content
        if len(submission.selftext) > 500:
            score += 10  # Detailed post
        elif len(submission.selftext) > 100:
            score += 5   # Some detail in post
        
        return score

    def rank_submissions(self, submissions: List[Submission]) -> List[Tuple[float, Submission]]:
        """
        Rank submissions by their engagement potential.
        
        Args:
            submissions (List[Submission]): List of submissions to rank
            
        Returns:
            List[Tuple[float, Submission]]: Submissions ranked by score (descending)
        """
        # Evaluate each submission
        scored_submissions = []
        for submission in submissions:
            # Skip submissions that are not relevant (stickied, etc.)
            if submission.stickied or (hasattr(submission, "distinguished") and submission.distinguished):
                continue
                
            # Skip meta posts
            title_lower = submission.title.lower()
            meta_keywords = ["rules", "announcement", "meta", "mod post", "moderator", "subreddit update"]
            if any(keyword in title_lower for keyword in meta_keywords):
                continue
            
            # Score the submission
            score = self.evaluate_submission_quality(submission)
            scored_submissions.append((score, submission))
        
        # Sort by score (descending)
        scored_submissions.sort(key=lambda x: x[0], reverse=True)
        return scored_submissions 