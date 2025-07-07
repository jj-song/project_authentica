#!/usr/bin/env python3
"""
Test script for enhanced prompt engineering with dynamic templates and variations.
"""

import os
import logging
from dotenv import load_dotenv
import json
import random

from src.config import get_reddit_instance
from src.llm_handler import generate_comment_from_submission
from src.context.collector import ContextCollector
from src.context.templates import TemplateSelector, PersonaBasedTemplate, ContentTypeTemplate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestEnhancedPrompts")

# Bot configuration
BOT_USERNAME = "my_first_bot"
SUBMISSION_ID = "1lu5snp"  # Replace with a real submission ID if needed


def test_context_collection():
    """Test the context collection functionality."""
    logger.info("Testing context collection...")
    reddit = get_reddit_instance(BOT_USERNAME)
    submission = reddit.submission(id=SUBMISSION_ID)
    
    collector = ContextCollector(reddit)
    context = collector.collect_context(submission)
    
    # Save context to file for inspection
    with open("context_data.json", "w") as f:
        # Convert any non-serializable objects to strings
        json.dump(context, f, default=str, indent=2)
    logger.info("Context data saved to context_data.json")
    
    return context, reddit, submission


def test_template_selection(context):
    """Test the template selection functionality."""
    logger.info("Testing template selection...")
    selector = TemplateSelector()
    
    # Test standard template selection
    template = selector.select_template(context)
    logger.info(f"Selected template: {template.__class__.__name__}")
    
    # Test each template type
    templates = {
        "standard": selector.templates["standard"],
        "subreddit_specific": selector.templates["subreddit_specific"],
        "persona_based": selector.templates["persona_based"],
        "content_type": selector.templates["content_type"],
    }
    
    for name, template in templates.items():
        logger.info(f"Testing {name} template...")
        prompt = template.generate(context)
        with open(f"prompt_{name}.txt", "w") as f:
            f.write(prompt)
        logger.info(f"{name.capitalize()} template prompt saved to prompt_{name}.txt")


def test_persona_templates(context):
    """Test each persona-based template."""
    logger.info("Testing persona-based templates...")
    
    for persona_key in PersonaBasedTemplate.PERSONAS.keys():
        logger.info(f"Testing persona: {persona_key}")
        template = PersonaBasedTemplate(persona_key)
        prompt = template.generate(context)
        
        with open(f"prompt_persona_{persona_key}.txt", "w") as f:
            f.write(prompt)
        logger.info(f"Persona '{persona_key}' prompt saved to prompt_persona_{persona_key}.txt")


def test_content_detection(context, submission):
    """Test content type detection."""
    logger.info("Testing content type detection...")
    
    content_template = ContentTypeTemplate()
    
    # Test each detection method
    is_question = content_template.is_question(context["submission"])
    is_discussion = content_template.is_discussion(context["submission"])
    is_advice_request = content_template.is_advice_request(context["submission"])
    
    logger.info(f"Content type detection results:")
    logger.info(f"  Is question: {is_question}")
    logger.info(f"  Is discussion: {is_discussion}")
    logger.info(f"  Is advice request: {is_advice_request}")


def test_variations(context):
    """Test the variation engine."""
    logger.info("Testing variation engine...")
    
    selector = TemplateSelector()
    
    # Test with different variation counts
    for count in [1, 2, 3]:
        logger.info(f"Testing with {count} variations...")
        prompt = selector.generate_with_variations(context, count)
        
        with open(f"prompt_with_{count}_variations.txt", "w") as f:
            f.write(prompt)
        logger.info(f"Prompt with {count} variations saved to prompt_with_{count}_variations.txt")


def test_comment_generation(reddit, submission):
    """Test the comment generation with the enhanced prompt system."""
    logger.info("Testing comment generation with enhanced prompt engineering...")
    
    # Generate comments with different variation counts
    for count in [1, 2, 3]:
        logger.info(f"Generating comment with {count} variations...")
        comment = generate_comment_from_submission(submission, reddit, count)
        
        with open(f"generated_comment_{count}_variations.txt", "w") as f:
            f.write(comment)
        logger.info(f"Comment with {count} variations saved to generated_comment_{count}_variations.txt")
        
        print(f"\nGenerated Comment with {count} variations:")
        print("-" * 50)
        print(comment)
        print("-" * 50)


def main():
    """Test the enhanced prompt engineering with dynamic templates and variations."""
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
        
        # Create output directory for test results
        os.makedirs("test_results", exist_ok=True)
        os.chdir("test_results")
        
        # Run tests
        context, reddit, submission = test_context_collection()
        test_template_selection(context)
        test_persona_templates(context)
        test_content_detection(context, submission)
        test_variations(context)
        test_comment_generation(reddit, submission)
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
