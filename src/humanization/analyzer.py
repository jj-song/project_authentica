#!/usr/bin/env python3
"""
Comment Analysis Module for Project Authentica.
Analyzes comments from target subreddits to learn human communication patterns.
"""

import logging
import re
import statistics
import string
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from collections import Counter

import praw
from praw.models import Comment, Submission, Subreddit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CommentAnalyzer:
    """
    Analyzes comments from target subreddits to learn human communication patterns.
    
    This class provides methods for:
    1. Collecting sample comments from subreddits
    2. Analyzing comment length distributions
    3. Detecting common linguistic patterns
    4. Identifying subreddit-specific language features
    """
    
    def __init__(self, reddit_instance: praw.Reddit, sample_size: int = 100):
        """
        Initialize the CommentAnalyzer.
        
        Args:
            reddit_instance (praw.Reddit): An authenticated Reddit instance
            sample_size (int): Number of comments to sample per subreddit
        """
        self.reddit = reddit_instance
        self.sample_size = sample_size
        self.common_typos = {
            'the': ['teh', 'hte', 'th'],
            'and': ['adn', 'nad', 'an'],
            'that': ['taht', 'tht'],
            'with': ['wiht', 'wtih'],
            'your': ['youre', 'ur', 'yor'],
            'you': ['u', 'yu'],
            'are': ['r', 'ar'],
            'would': ['woud', 'wuld'],
            'because': ['becuase', 'cuz', 'bcuz', 'bc'],
            'though': ['tho', 'thou'],
        }
    
    def collect_comments(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Collect sample comments from a subreddit.
        
        Args:
            subreddit_name (str): Name of the subreddit to sample
            
        Returns:
            List[Dict[str, Any]]: List of comment data dictionaries
        """
        logger.info(f"Collecting {self.sample_size} comments from r/{subreddit_name}")
        
        subreddit = self.reddit.subreddit(subreddit_name)
        comments = []
        
        # Collect from hot posts
        for submission in subreddit.hot(limit=10):
            if len(comments) >= self.sample_size:
                break
                
            submission.comments.replace_more(limit=0)  # Flatten comment forest
            
            for comment in submission.comments.list():
                # Skip deleted/removed comments, bot comments, and very short comments
                if (not comment.author or 
                    comment.body in ['[deleted]', '[removed]'] or 
                    'bot' in str(comment.author).lower() or
                    len(comment.body) < 20):
                    continue
                
                comments.append({
                    'id': comment.id,
                    'author': str(comment.author),
                    'body': comment.body,
                    'score': comment.score,
                    'created_utc': comment.created_utc,
                    'submission_id': submission.id,
                    'is_top_level': comment.parent_id.startswith('t3_')
                })
                
                if len(comments) >= self.sample_size:
                    break
        
        logger.info(f"Collected {len(comments)} comments from r/{subreddit_name}")
        return comments
    
    def analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a collection of comments to extract patterns.
        
        Args:
            comments (List[Dict[str, Any]]): List of comment data dictionaries
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        if not comments:
            logger.warning("No comments provided for analysis")
            return {}
        
        # Extract comment bodies
        comment_bodies = [comment['body'] for comment in comments]
        
        # Analyze various aspects
        length_stats = self._analyze_length(comment_bodies)
        structure_stats = self._analyze_structure(comment_bodies)
        vocabulary_stats = self._analyze_vocabulary(comment_bodies)
        informality_stats = self._analyze_informality(comment_bodies)
        
        # Combine all stats
        analysis = {
            'comment_count': len(comments),
            'length': length_stats,
            'structure': structure_stats,
            'vocabulary': vocabulary_stats,
            'informality': informality_stats
        }
        
        return analysis
    
    def _analyze_length(self, comment_bodies: List[str]) -> Dict[str, Any]:
        """
        Analyze the length distribution of comments.
        
        Args:
            comment_bodies (List[str]): List of comment text bodies
            
        Returns:
            Dict[str, Any]: Length statistics
        """
        char_lengths = [len(body) for body in comment_bodies]
        word_lengths = [len(body.split()) for body in comment_bodies]
        sentence_counts = [len(re.split(r'[.!?]+', body)) for body in comment_bodies]
        
        return {
            'char_length': {
                'mean': statistics.mean(char_lengths),
                'median': statistics.median(char_lengths),
                'stdev': statistics.stdev(char_lengths) if len(char_lengths) > 1 else 0,
                'min': min(char_lengths),
                'max': max(char_lengths),
                'p25': np.percentile(char_lengths, 25),
                'p75': np.percentile(char_lengths, 75)
            },
            'word_length': {
                'mean': statistics.mean(word_lengths),
                'median': statistics.median(word_lengths),
                'stdev': statistics.stdev(word_lengths) if len(word_lengths) > 1 else 0,
                'min': min(word_lengths),
                'max': max(word_lengths)
            },
            'sentence_count': {
                'mean': statistics.mean(sentence_counts),
                'median': statistics.median(sentence_counts),
                'stdev': statistics.stdev(sentence_counts) if len(sentence_counts) > 1 else 0
            }
        }
    
    def _analyze_structure(self, comment_bodies: List[str]) -> Dict[str, Any]:
        """
        Analyze the structure of comments.
        
        Args:
            comment_bodies (List[str]): List of comment text bodies
            
        Returns:
            Dict[str, Any]: Structure statistics
        """
        # Count paragraphs
        paragraph_counts = [len(re.split(r'\n\s*\n', body)) for body in comment_bodies]
        
        # Check for bullet points/numbered lists
        has_bullets = [1 if re.search(r'(\n\s*[-*•]|\n\s*\d+\.)', body) else 0 for body in comment_bodies]
        
        # Check for quotes
        has_quotes = [1 if re.search(r'(&gt;|>).*?(\n|$)', body) else 0 for body in comment_bodies]
        
        # Check for links
        has_links = [1 if re.search(r'\[.*?\]\(.*?\)', body) or 'http' in body else 0 for body in comment_bodies]
        
        return {
            'paragraph_count': {
                'mean': statistics.mean(paragraph_counts),
                'median': statistics.median(paragraph_counts)
            },
            'has_bullets_ratio': sum(has_bullets) / len(has_bullets) if has_bullets else 0,
            'has_quotes_ratio': sum(has_quotes) / len(has_quotes) if has_quotes else 0,
            'has_links_ratio': sum(has_links) / len(has_links) if has_links else 0
        }
    
    def _analyze_vocabulary(self, comment_bodies: List[str]) -> Dict[str, Any]:
        """
        Analyze vocabulary usage in comments.
        
        Args:
            comment_bodies (List[str]): List of comment text bodies
            
        Returns:
            Dict[str, Any]: Vocabulary statistics
        """
        # Join all comments and split into words
        all_text = ' '.join(comment_bodies).lower()
        words = re.findall(r'\b\w+\b', all_text)
        
        # Count word frequencies
        word_counter = Counter(words)
        common_words = word_counter.most_common(20)
        
        # Calculate lexical diversity
        unique_words = len(set(words))
        total_words = len(words)
        lexical_diversity = unique_words / total_words if total_words > 0 else 0
        
        return {
            'common_words': common_words,
            'lexical_diversity': lexical_diversity,
            'unique_word_count': unique_words,
            'total_word_count': total_words
        }
    
    def _analyze_informality(self, comment_bodies: List[str]) -> Dict[str, Any]:
        """
        Analyze informality markers in comments.
        
        Args:
            comment_bodies (List[str]): List of comment text bodies
            
        Returns:
            Dict[str, Any]: Informality statistics
        """
        # Check for contractions
        contraction_pattern = r"\b\w+['']\w+\b"
        contraction_counts = [len(re.findall(contraction_pattern, body)) for body in comment_bodies]
        
        # Check for emoji/emoticons
        emoji_pattern = r'(?::|;|=)(?:-)?(?:\)|D|P|p|\(|O|o|/|\\|\[|\])'
        emoji_counts = [len(re.findall(emoji_pattern, body)) for body in comment_bodies]
        
        # Check for all caps words (excitement/emphasis)
        caps_pattern = r'\b[A-Z]{2,}\b'
        caps_counts = [len(re.findall(caps_pattern, body)) for body in comment_bodies]
        
        # Check for multiple punctuation (!!!???)
        multi_punct_pattern = r'[!?]{2,}'
        multi_punct_counts = [len(re.findall(multi_punct_pattern, body)) for body in comment_bodies]
        
        # Check for informal abbreviations
        abbrev_pattern = r'\b(lol|omg|lmao|wtf|idk|imo|tbh|iirc|afaik|ftfy|smh|fwiw|til|tl;dr|ymmv)\b'
        abbrev_counts = [len(re.findall(abbrev_pattern, body.lower())) for body in comment_bodies]
        
        return {
            'contraction_rate': statistics.mean(contraction_counts) if contraction_counts else 0,
            'emoji_rate': statistics.mean(emoji_counts) if emoji_counts else 0,
            'caps_rate': statistics.mean(caps_counts) if caps_counts else 0,
            'multi_punct_rate': statistics.mean(multi_punct_counts) if multi_punct_counts else 0,
            'abbrev_rate': statistics.mean(abbrev_counts) if abbrev_counts else 0,
            'informality_score': self._calculate_informality_score(
                contraction_counts, emoji_counts, caps_counts, multi_punct_counts, abbrev_counts
            )
        }
    
    def _calculate_informality_score(self, *feature_lists) -> float:
        """
        Calculate an overall informality score based on various features.
        
        Args:
            *feature_lists: Lists of feature counts
            
        Returns:
            float: Informality score between 0 and 1
        """
        # Simple weighted average of normalized feature rates
        feature_means = [statistics.mean(feature) if feature else 0 for feature in feature_lists]
        
        # Normalize by typical maximums
        max_values = [3, 2, 2, 2, 3]  # Typical max values for each feature
        normalized = [min(mean / max_val, 1) for mean, max_val in zip(feature_means, max_values)]
        
        # Weighted average (equal weights for now)
        weights = [0.25, 0.2, 0.2, 0.2, 0.15]
        informality_score = sum(n * w for n, w in zip(normalized, weights))
        
        return informality_score
    
    def get_subreddit_profile(self, subreddit_name: str) -> Dict[str, Any]:
        """
        Generate a complete profile of a subreddit's comment patterns.
        
        Args:
            subreddit_name (str): Name of the subreddit to profile
            
        Returns:
            Dict[str, Any]: Subreddit comment profile
        """
        comments = self.collect_comments(subreddit_name)
        analysis = self.analyze_comments(comments)
        
        # Add subreddit metadata
        subreddit = self.reddit.subreddit(subreddit_name)
        analysis['subreddit'] = {
            'name': subreddit_name,
            'display_name': subreddit.display_name,
            'subscribers': subreddit.subscribers,
            'description': subreddit.public_description or subreddit.description
        }
        
        # Add sample comments (for examples)
        if comments:
            # Sort by score and select a few good examples
            good_comments = sorted(comments, key=lambda c: c['score'], reverse=True)[:5]
            analysis['sample_comments'] = good_comments
        
        return analysis


if __name__ == "__main__":
    # Example usage
    import os
    from src.config import get_reddit_instance
    
    reddit = get_reddit_instance(os.getenv("BOT_USERNAME", "my_first_bot"))
    analyzer = CommentAnalyzer(reddit, sample_size=50)
    
    subreddit_name = "formula1"
    profile = analyzer.get_subreddit_profile(subreddit_name)
    
    print(f"=== Comment Profile for r/{subreddit_name} ===")
    print(f"Average comment length: {profile['length']['char_length']['mean']:.1f} characters")
    print(f"Average word count: {profile['length']['word_length']['mean']:.1f} words")
    print(f"Informality score: {profile['informality']['informality_score']:.2f} (0-1 scale)")
    
    if 'sample_comments' in profile:
        print("\nSample comment:")
        sample = profile['sample_comments'][0]
        print(f"Comment by {sample['author']} (Score: {sample['score']}):")
        print(sample['body'][:200] + "..." if len(sample['body']) > 200 else sample['body']) 