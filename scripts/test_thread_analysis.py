#!/usr/bin/env python3
"""
Test script for the thread analysis functionality.
"""

import sys
import os
import json
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import get_reddit_instance
from src.thread_analysis.analyzer import ThreadAnalyzer
from src.thread_analysis.conversation import ConversationFlow
from src.thread_analysis.strategies import ResponseStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ThreadAnalysisTest")


def main():
    """Test the thread analysis functionality."""
    # Get Reddit instance
    reddit = get_reddit_instance("my_first_bot")
    logger.info(f"Authenticated as {reddit.user.me()}")
    
    # Create thread analyzer
    analyzer = ThreadAnalyzer(reddit)
    
    # Get submission ID from command line or use default
    submission_id = sys.argv[1] if len(sys.argv) > 1 else "1lv6oae"  # Default to a test post
    
    # Get the submission
    submission = reddit.submission(submission_id)
    logger.info(f"Analyzing thread: {submission.title} (ID: {submission.id})")
    
    # Perform thread analysis
    analysis = analyzer.analyze_thread(submission)
    
    # Print analysis results
    print("\n=== THREAD ANALYSIS RESULTS ===\n")
    
    # Print basic stats
    print(f"Comment count: {analysis['comment_count']}")
    print(f"Thread depth: {analysis['thread_depth']}")
    print(f"Key topics: {', '.join(analysis['key_topics'])}")
    print(f"Overall sentiment: {analysis['sentiment']['overall']}")
    print(f"Sentiment distribution: {json.dumps(analysis['sentiment']['distribution'])}")
    
    # Print conversation flow stats
    print("\n=== CONVERSATION FLOW ===\n")
    print(f"Branching factor: {analysis['conversation_flow']['branching_factor']:.2f}")
    print(f"Max chain length: {analysis['conversation_flow']['max_chain_length']}")
    print(f"Avg chain length: {analysis['conversation_flow']['avg_chain_length']:.2f}")
    print(f"Conversation density: {analysis['conversation_flow']['conversation_density']:.2f}")
    print(f"Reply patterns: {json.dumps(analysis['conversation_flow']['reply_patterns'])}")
    
    # Print top discussion hotspots
    print("\n=== DISCUSSION HOTSPOTS ===\n")
    for i, hotspot in enumerate(analysis['conversation_flow']['discussion_hotspots'][:3], 1):
        print(f"Hotspot {i}:")
        print(f"  Comment ID: {hotspot['comment_id']}")
        print(f"  Author: {hotspot['author']}")
        print(f"  Reply count: {hotspot['reply_count']}")
        print(f"  Score: {hotspot['score']}")
        print(f"  Hotspot score: {hotspot['hotspot_score']}")
        print()
    
    # Print user engagement
    print("\n=== USER ENGAGEMENT ===\n")
    print(f"Unique users: {len(analysis['user_engagement']['unique_users'])}")
    print(f"Submitter engagement: {analysis['user_engagement']['submitter_engagement']} comments")
    
    # Print top contributors
    print("\n=== TOP CONTRIBUTORS ===\n")
    for i, contributor in enumerate(analysis['top_contributors'][:5], 1):
        print(f"{i}. {contributor['username']}: {contributor['comment_count']} comments, avg score: {contributor['avg_score']:.1f}")
    
    # Generate response strategy
    from src.context.collector import ContextCollector
    collector = ContextCollector(reddit)
    context = collector.collect_context(submission)
    
    strategy_generator = ResponseStrategy()
    strategy = strategy_generator.determine_strategy(analysis, context)
    
    # Print strategy
    print("\n=== RESPONSE STRATEGY ===\n")
    print(f"Selected strategy: {strategy['type']}")
    print(f"Reasoning: {strategy['reasoning']}")
    
    if strategy['target_comment']:
        print(f"Target comment: {strategy['target_comment']['id']} by {strategy['target_comment']['author']}")
    else:
        print("Target: Direct reply to submission")
    
    print("\nPrompt enhancements:")
    for key, value in strategy['prompt_enhancements'].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main() 