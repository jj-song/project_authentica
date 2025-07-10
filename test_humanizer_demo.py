#!/usr/bin/env python3
"""
Demo script to show the humanization features in action.
This script doesn't require any API keys or external services.
"""

import sys
import os
import random

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the humanizer
from src.humanizer import TextHumanizer, humanize_text

# Sample Reddit-style comments to humanize
SAMPLE_COMMENTS = [
    """
    Python is definitely my favorite language for beginners. The syntax is clean and readable, 
    and there are so many great libraries and resources available. I started with C++ in college 
    and it was much harder to grasp the concepts. Python lets you focus on the logic rather than 
    the syntax. I would recommend starting with some simple projects like a calculator or a todo 
    list to get comfortable with the basics.
    """,
    
    """
    I've been a software engineer for 10 years, and I still think JavaScript is essential to learn. 
    The web isn't going anywhere, and JavaScript is the language of the web. React, Vue, and Angular 
    are all built on JavaScript, and knowing it well will open up a lot of job opportunities. 
    That said, it has its quirks and inconsistencies that can be frustrating at times.
    """,
    
    """
    For someone just starting out, I would recommend focusing on problem-solving skills rather than 
    specific languages. Once you understand programming concepts like variables, loops, conditionals, 
    and functions, you can pick up new languages relatively quickly. That said, Python is a great first 
    language because of its readability and large community. JavaScript is also important if you're 
    interested in web development.
    """,
    
    """
    I've been using TypeScript for about 2 years now, and it's significantly improved my JavaScript 
    development experience. The static typing catches so many bugs before they even make it to runtime. 
    It takes a bit of time to set up properly and learn the type system, but the investment pays off 
    quickly. If you're already comfortable with JavaScript, I highly recommend giving TypeScript a try.
    """
]

def demo_humanization():
    """Demonstrate the humanization features with sample comments."""
    print("\n===== HUMANIZATION DEMO =====\n")
    print("This demo shows how the humanizer transforms perfectly written text")
    print("into more natural, human-like responses with varying levels of imperfection.\n")
    
    # Select a random comment
    original_comment = random.choice(SAMPLE_COMMENTS)
    
    # Show the original
    print("ORIGINAL COMMENT:")
    print("-" * 80)
    print(original_comment.strip())
    print("-" * 80)
    print()
    
    # Show different humanization levels
    levels = [0.3, 0.7, 1.0]
    for level in levels:
        humanized = humanize_text(original_comment, level)
        print(f"HUMANIZED (Level {level}):")
        print("-" * 80)
        print(humanized)
        print("-" * 80)
        print()
    
    # Show different humanization effects
    print("\n===== HUMANIZATION EFFECTS =====\n")
    
    # Create a humanizer with high level
    humanizer = TextHumanizer(humanization_level=0.9)
    
    # Original text for specific effects
    text = "I believe that Python is the best programming language for beginners because it has a clean syntax and is very readable."
    
    # Show specific effects
    print("ORIGINAL TEXT:")
    print(text)
    print()
    
    # Apply typos
    typo_text = humanizer._add_typos(text)
    print("WITH TYPOS:")
    print(typo_text)
    print()
    
    # Apply contractions
    contraction_text = humanizer._apply_contractions(text)
    print("WITH CONTRACTIONS:")
    print(contraction_text)
    print()
    
    # Apply abbreviations
    abbr_text = humanizer._apply_abbreviations(text)
    print("WITH ABBREVIATIONS:")
    print(abbr_text)
    print()
    
    # Apply punctuation modifications
    punct_text = humanizer._modify_punctuation(text)
    print("WITH PUNCTUATION MODIFICATIONS:")
    print(punct_text)
    print()
    
    # Apply capitalization modifications
    cap_text = humanizer._modify_capitalization(text)
    print("WITH CAPITALIZATION MODIFICATIONS:")
    print(cap_text)
    print()
    
    # Apply self-corrections
    correction_text = humanizer._add_self_corrections(text)
    print("WITH SELF-CORRECTIONS:")
    print(correction_text)
    print()

if __name__ == "__main__":
    demo_humanization() 