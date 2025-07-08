#!/usr/bin/env python3
"""
Show the context collected for a Reddit submission.
This demonstrates what information is being collected for dynamic prompt engineering.
"""

import sys
import os
import json
import praw

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import get_reddit_instance
from src.context.collector import ContextCollector

def main():
    """Show the context collected for a Reddit submission."""
    # Get Reddit instance
    reddit = get_reddit_instance("my_first_bot")
    print(f"Authenticated as {reddit.user.me()}")
    
    # Create context collector
    collector = ContextCollector(reddit)
    
    # Get a submission (using the one we created earlier)
    submission_id = "1lu9d24"  # ID of our test post
    submission = reddit.submission(submission_id)
    
    print(f"\nCollecting context for submission: {submission.title}")
    
    # Collect context
    context = collector.collect_context(submission)
    
    # Print the context in a readable format
    print("\n=== COLLECTED CONTEXT ===\n")
    print(json.dumps(context, indent=2))
    
    # Show what templates would be selected
    from src.context.templates import TemplateSelector
    selector = TemplateSelector()
    template = selector.select_template(context)
    
    print(f"\n=== SELECTED TEMPLATE ===\n")
    print(f"Template type: {template.__class__.__name__}")
    
    # Show what variations would be applied
    from src.context.templates import VariationEngine
    variations = VariationEngine.get_random_variations(2)
    
    print(f"\n=== SELECTED VARIATIONS ===\n")
    for i, variation in enumerate(variations, 1):
        print(f"Variation {i}: {variation}")

if __name__ == "__main__":
    main() 