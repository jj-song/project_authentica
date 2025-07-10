#!/usr/bin/env python3
"""
LLM Handler module for Project Authentica.
Manages all interactions with external Large Language Models.
"""

import os
import time
import logging
import json
from typing import Optional, Dict, Any, Union, List

from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import praw
from praw.models import Submission, Comment

from src.context.collector import ContextCollector
from src.context.templates import TemplateSelector
from src.database import get_db_connection

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default values if environment variables are not set
DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 250

# Get configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", DEFAULT_MODEL)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", DEFAULT_TEMPERATURE))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", DEFAULT_MAX_TOKENS))


def create_prompt(submission: Submission, reddit_instance: praw.Reddit, variation_count: int = 2, comment_to_reply: Optional[Comment] = None) -> str:
    """
    Format the submission into an effective prompt for the LLM using context-aware prompt engineering.
    
    Args:
        submission (Submission): The Reddit submission
        reddit_instance (praw.Reddit): Authenticated Reddit instance for context collection
        variation_count (int): Number of variations to apply to the prompt
        comment_to_reply (Optional[Comment]): If provided, generate a reply to this comment instead of the submission.
        
    Returns:
        str: A formatted prompt for the LLM
    """
    try:
        # Collect context
        collector = ContextCollector(reddit_instance)
        context = collector.collect_context(submission)
        
        # If thread analysis is enabled, perform advanced analysis
        if os.getenv("ENABLE_THREAD_ANALYSIS", "").lower() == "true":
            try:
                from src.thread_analysis.analyzer import ThreadAnalyzer
                from src.thread_analysis.strategies import ResponseStrategy
                
                # Perform thread analysis
                analyzer = ThreadAnalyzer(reddit_instance)
                thread_analysis = analyzer.analyze_thread(submission)
                
                # Determine response strategy
                strategy_generator = ResponseStrategy()
                strategy = strategy_generator.determine_strategy(thread_analysis, context)
                
                # Add strategy information to context
                context["thread_analysis"] = thread_analysis
                context["response_strategy"] = strategy
                
                logger.info(f"Using response strategy: {strategy['type']}")
                
                # If strategy specifies a target comment and we don't already have one, use it
                if strategy["target_comment"] and not comment_to_reply:
                    # Find the comment in the submission
                    for comment in submission.comments.list():
                        if hasattr(comment, "id") and comment.id == strategy["target_comment"].get("id"):
                            comment_to_reply = comment
                            break
            except ImportError:
                logger.warning("Thread analysis modules not available, skipping advanced analysis")
            except Exception as e:
                logger.error(f"Error in thread analysis: {str(e)}")
        
        # Select template and generate base prompt with variations
        selector = TemplateSelector()
        base_prompt = selector.generate_with_variations(context, variation_count, comment_to_reply)
        
        # If humanization is enabled, enhance the prompt with human-like examples and guidelines
        if os.getenv("ENABLE_HUMANIZATION", "").lower() == "true":
            try:
                from src.humanization.sampler import CommentSampler
                from src.humanization.prompt_enhancer import enhance_prompt
                
                # Get database connection
                db_conn = get_db_connection()
                
                # Create sampler and get samples and profile
                sampler = CommentSampler(reddit_instance, db_conn)
                subreddit_name = str(submission.subreddit)
                
                # Get representative samples and subreddit profile
                samples = sampler.get_representative_samples(subreddit_name, context, count=3)
                profile = sampler.get_subreddit_profile(subreddit_name)
                
                # Enhance the prompt with humanization
                enhanced_prompt = enhance_prompt(base_prompt, samples, profile, context)
                
                # Close database connection
                db_conn.close()
                
                logger.info(f"Enhanced prompt with humanization for r/{subreddit_name}")
                return enhanced_prompt
            except Exception as e:
                logger.error(f"Error enhancing prompt with humanization: {str(e)}")
                # Fall back to base prompt if humanization fails
                return base_prompt
        
        return base_prompt
    except Exception as e:
        logger.error(f"Error creating context-aware prompt: {str(e)}")
        # Fall back to basic prompt if context collection fails
        return _create_basic_prompt(submission.title, submission.selftext)


def _create_basic_prompt(title: str, body: str) -> str:
    """
    Format the submission into a basic prompt for the LLM (fallback method).
    
    Args:
        title (str): The title of the Reddit submission
        body (str): The body/content of the Reddit submission
        
    Returns:
        str: A formatted prompt for the LLM
    """
    return f"""
    Please write a helpful, informative Reddit comment responding to this post:
    
    Title: {title}
    
    Content: {body}
    
    Your comment should be:
    - Helpful and informative
    - Friendly and conversational
    - Under 500 characters
    - Without any prefixes like 'Here's my response:'
    """


@retry(
    wait=wait_exponential(min=1, max=60),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
def call_openai_api(prompt: str, verbose: bool = False) -> str:
    """
    Make the API call to OpenAI with retry logic.
    
    Args:
        prompt (str): The formatted prompt to send to the API
        verbose (bool): Whether to print detailed information
        
    Returns:
        str: The generated text response
        
    Raises:
        Exception: If the API call fails after retries
    """
    if not OPENAI_API_KEY:
        logger.warning("OpenAI API key not found. Using placeholder response.")
        return "This is a helpful, AI-generated placeholder comment."
    
    if verbose:
        print("\n=== PROMPT SENT TO LLM ===\n")
        print(prompt)
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Make the API call
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful Reddit commenter providing valuable information."},
                {"role": "user", "content": prompt}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            top_p=1.0
        )
        
        # Extract the generated text
        generated_text = response.choices[0].message.content.strip()
        
        if verbose:
            print("\n=== LLM RESPONSE ===\n")
            print(generated_text)
            
        return generated_text
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise


def clean_response(text: str) -> str:
    """
    Clean and format the API response.
    
    Args:
        text (str): The raw text from the API
        
    Returns:
        str: Cleaned and formatted text suitable for a Reddit comment
    """
    # Remove any markdown formatting that might cause issues
    # For now, just do basic cleaning
    
    # Ensure the comment is within Reddit's character limits (10,000 characters)
    if len(text) > 10000:
        text = text[:9997] + "..."
    
    return text


def generate_comment_from_submission(submission: Submission, reddit_instance: praw.Reddit, variation_count: int = 2, comment_to_reply: Optional[Comment] = None, verbose: bool = False) -> str:
    """
    Generate a comment for a Reddit submission using an external LLM with context-aware prompting.
    
    This function takes a Reddit submission and uses context-aware prompt engineering
    to generate a relevant, helpful comment using OpenAI's API.
    
    Args:
        submission (Submission): The Reddit submission.
        reddit_instance (praw.Reddit): Authenticated Reddit instance for context collection.
        variation_count (int): Number of variations to apply to the prompt.
        comment_to_reply (Optional[Comment]): If provided, generate a reply to this comment instead of the submission.
        verbose (bool): Whether to print detailed information about the process.
        
    Returns:
        str: A generated comment that is relevant to the submission.
        
    Note:
        If the API call fails, this will return a hardcoded placeholder string.
    """
    try:
        # Create the context-aware prompt with variations
        prompt = create_prompt(submission, reddit_instance, variation_count, comment_to_reply)
        
        # Log the prompt for debugging (but not in production)
        if os.getenv("DEBUG_MODE", "").lower() == "true" or verbose:
            logger.debug(f"Generated prompt:\n{prompt}")
        
        # Call the API
        generated_text = call_openai_api(prompt, verbose)
        
        # Process and return the response
        return clean_response(generated_text)
    except Exception as e:
        logger.error(f"Failed to generate comment: {str(e)}")
        return "This is a helpful, AI-generated placeholder comment."


def generate_comment(submission_title: str, submission_body: str) -> str:
    """
    Generate a comment for a Reddit submission using an external LLM.
    
    This function takes the title and body of a Reddit submission as context
    and uses them to generate a relevant, helpful comment using OpenAI's API.
    
    This is a legacy method maintained for backward compatibility.
    
    Args:
        submission_title (str): The title of the Reddit submission.
        submission_body (str): The body/content of the Reddit submission.
        
    Returns:
        str: A generated comment that is relevant to the submission.
        
    Note:
        If the API call fails, this will return a hardcoded placeholder string.
        
    Example:
        >>> title = "Need help with Python dictionary"
        >>> body = "I'm trying to merge two dictionaries but getting errors."
        >>> comment = generate_comment(title, body)
    """
    try:
        # Create the basic prompt
        prompt = _create_basic_prompt(submission_title, submission_body)
        
        # Call the API
        generated_text = call_openai_api(prompt)
        
        # Process and return the response
        return clean_response(generated_text)
    except Exception as e:
        logger.error(f"Failed to generate comment: {str(e)}")
        return "This is a helpful, AI-generated placeholder comment."


if __name__ == "__main__":
    # Example usage
    from src.config import get_reddit_instance
    
    # Get Reddit instance
    reddit = get_reddit_instance("my_first_bot")
    
    # Get a submission
    submission_id = "1lu5snp"  # Replace with a real submission ID
    submission = reddit.submission(id=submission_id)
    
    print(f"Generating comment for the following post:")
    print(f"Title: {submission.title}")
    print(f"Body: {submission.selftext[:100]}...")
    print()
    
    print("Generating comment...")
    comment = generate_comment_from_submission(submission, reddit)
    
    print("\nGenerated Comment:")
    print("-" * 50)
    print(comment)
    print("-" * 50)
