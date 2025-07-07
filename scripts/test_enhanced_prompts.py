#!/usr/bin/env python3
"""
Test script for enhanced prompt engineering.
"""

import os
import logging
from dotenv import load_dotenv
import json

from src.config import get_reddit_instance
from src.llm_handler import generate_comment_from_submission
from src.context.collector import ContextCollector
from src.context.templates import TemplateSelector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestEnhancedPrompts")

# Bot configuration
BOT_USERNAME = "my_first_bot"
SUBMISSION_ID = "1lu5snp"  # Replace with a real submission ID if needed


def main():
    """Test the enhanced prompt engineering."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Check if API key is set
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY environment variable is not set.")
            return
        
        # Get Reddit instance
        logger.info(f"Authenticating as {BOT_USERNAME}...")
        reddit = get_reddit_instance(BOT_USERNAME)
        logger.info(f"Successfully authenticated as {reddit.user.me()}")
        
        # Get the submission
        submission = reddit.submission(id=SUBMISSION_ID)
        logger.info(f"Retrieved submission: {submission.title}")
        
        # Test context collection
        logger.info("Testing context collection...")
        collector = ContextCollector(reddit)
        context = collector.collect_context(submission)
        
        # Save context to file for inspection
        with open("context_data.json", "w") as f:
            # Convert any non-serializable objects to strings
            json.dump(context, f, default=str, indent=2)
        logger.info("Context data saved to context_data.json")
        
        # Test template selection
        logger.info("Testing template selection...")
        selector = TemplateSelector()
        template = selector.select_template(context)
        logger.info(f"Selected template: {template.__class__.__name__}")
        
        # Generate prompt
        prompt = template.generate(context)
        
        # Save prompt to file for inspection
        with open("generated_prompt.txt", "w") as f:
            f.write(prompt)
        logger.info("Generated prompt saved to generated_prompt.txt")
        
        # Generate comment
        logger.info("Generating comment with enhanced prompt engineering...")
        comment = generate_comment_from_submission(submission, reddit)
        
        # Save comment to file for inspection
        with open("generated_comment.txt", "w") as f:
            f.write(comment)
        logger.info("Generated comment saved to generated_comment.txt")
        
        # Print the comment
        print("\nGenerated Comment:")
        print("-" * 50)
        print(comment)
        print("-" * 50)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
