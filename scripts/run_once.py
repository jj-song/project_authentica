#!/usr/bin/env python3
"""
Run the Authentica agent once without the scheduler.
This script is a wrapper around the run_once function in src/main.py.
"""

import sys
import os
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import run_once

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run Project Authentica once without the scheduler.')
    
    parser.add_argument('--subreddit', '-s', type=str, default='formula1',
                        help='Subreddit to scan (default: formula1)')
    
    parser.add_argument('--limit', '-l', type=int, default=1,
                        help='Maximum number of posts to process (default: 1)')
    
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Run in quiet mode (less verbose output)')
    
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # Enable thread analysis
    os.environ["ENABLE_THREAD_ANALYSIS"] = "true"
    
    # Run once with the specified arguments
    run_once(
        subreddit_name=args.subreddit,
        post_limit=args.limit,
        verbose=not args.quiet
    )
