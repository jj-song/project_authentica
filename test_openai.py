#!/usr/bin/env python3
"""
Script to test the OpenAI integration manually.
"""

import os
import sys
from dotenv import load_dotenv
from src.llm_handler import generate_comment

def main():
    """Test the OpenAI integration with a sample Reddit post."""
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please create a .env file with your OpenAI API key or set it in your environment.")
        print("Example: OPENAI_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Sample Reddit post
    title = "Need help with my Python code"
    body = """
    I'm trying to write a function that calculates the factorial of a number, but I'm getting a recursion error when I try to run it. Here's my code:
    
    ```python
    def factorial(n):
        return n * factorial(n-1)
    ```
    
    What am I doing wrong?
    """
    
    print("Generating comment for the following post:")
    print(f"Title: {title}")
    print(f"Body: {body[:100]}...")
    print("\nGenerating comment...")
    
    # Generate comment
    comment = generate_comment(title, body)
    
    print("\nGenerated Comment:")
    print("-" * 50)
    print(comment)
    print("-" * 50)

if __name__ == "__main__":
    main() 