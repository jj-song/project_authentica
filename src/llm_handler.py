#!/usr/bin/env python3
"""
LLM Handler module for Project Authentica.
Manages all interactions with external Large Language Models.
"""

import os
import time
import logging
from typing import Optional, Dict, Any, Union, List

from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import praw
from praw.models import Submission, Comment

from src.response_generator import ResponseGenerator
from src.utils.logging_utils import get_component_logger
from src.utils.error_utils import handle_exceptions, LLMError
from src.config import init_configuration

# Configure logging
logger = get_component_logger("llm_handler")

# Get configuration
config = init_configuration()

# Get OpenAI configuration
OPENAI_API_KEY = config["openai"]["api_key"]
LLM_MODEL = config["openai"]["model"]
LLM_TEMPERATURE = config["openai"]["temperature"]
LLM_MAX_TOKENS = config["openai"]["max_tokens"]


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
        LLMError: If the API call fails after retries
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
        generated_text = response.choices[0].message.content
        
        if verbose:
            print("\n=== RAW LLM RESPONSE ===\n")
            print(generated_text)
        
        return generated_text
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise LLMError(f"OpenAI API error: {str(e)}")


def clean_response(text: str) -> str:
    """
    Clean up the LLM response to make it suitable for posting.
    
    Args:
        text (str): The raw text from the LLM
        
    Returns:
        str: Cleaned text ready for posting
    """
    # Remove any markdown code block formatting
    text = text.replace("```", "")
    
    # Remove any "As an AI" disclaimers
    disclaimers = [
        "as an ai", "as an artificial intelligence", "as a language model",
        "i'm an ai", "i am an ai", "i'm a language model", "i am a language model"
    ]
    
    lines = text.split("\n")
    filtered_lines = []
    for line in lines:
        if not any(disclaimer in line.lower() for disclaimer in disclaimers):
            filtered_lines.append(line)
    
    text = "\n".join(filtered_lines)
    
    # Remove any leading/trailing whitespace
    text = text.strip()
    
    return text


# This function is deprecated - use ResponseGenerator directly instead
# Keeping for backward compatibility but will be removed in future versions
@handle_exceptions
def generate_comment_from_submission(submission: Submission, reddit_instance: praw.Reddit, variation_count: int = 2, comment_to_reply: Optional[Comment] = None, verbose: bool = False) -> str:
    """
    DEPRECATED: Use ResponseGenerator directly instead.
    Generate a comment for a Reddit submission using the ResponseGenerator pipeline.
    
    Args:
        submission (Submission): The Reddit submission
        reddit_instance (praw.Reddit): Authenticated Reddit instance
        variation_count (int): Number of variations to apply
        comment_to_reply (Optional[Comment]): If provided, generate a reply to this comment
        verbose (bool): Whether to print detailed information
        
    Returns:
        str: The generated comment text
    """
    logger.warning("generate_comment_from_submission is deprecated - use ResponseGenerator directly")
    
    # Use ResponseGenerator directly (this is now the proper way)
    response_generator = ResponseGenerator(reddit_instance)
    response_data = response_generator.generate_response(
        submission=submission,
        comment_to_reply=comment_to_reply,
        variation_count=variation_count,
        verbose=verbose
    )
    
    return response_data["text"]


def generate_comment(submission_title: str, submission_body: str) -> str:
    """
    Generate a comment for a Reddit submission using just the title and body.
    This is a simplified version for testing and direct API calls.
    
    Args:
        submission_title (str): The title of the submission
        submission_body (str): The body/content of the submission
        
    Returns:
        str: The generated comment text
    """
    logger.info("Generating comment using basic prompt")
    
    try:
        # Create a basic prompt
        prompt = _create_basic_prompt(submission_title, submission_body)
        
        # Call the OpenAI API
        raw_response = call_openai_api(prompt)
        
        # Clean up the response
        clean_comment = clean_response(raw_response)
        
        return clean_comment
    except Exception as e:
        logger.error(f"Error generating comment: {str(e)}")
        return "Sorry, I couldn't generate a response at this time."


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
