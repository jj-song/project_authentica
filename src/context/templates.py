#!/usr/bin/env python3
"""
Prompt template module for Project Authentica.
Provides templates for generating prompts based on context.
"""

import random
from typing import Dict, Any, List, Optional


class PromptTemplate:
    """
    Base class for prompt templates.
    
    This class provides methods for generating prompts based on context.
    """
    
    def generate(self, context: Dict[str, Any]) -> str:
        """
        Generate a prompt based on context.
        
        Args:
            context (Dict[str, Any]): Context information.
            
        Returns:
            str: The generated prompt.
        """
        raise NotImplementedError("Subclasses must implement generate()")


class StandardPromptTemplate(PromptTemplate):
    """
    Standard prompt template for general use.
    
    This template generates a prompt that includes:
    - Submission title and body
    - Subreddit information
    - Comment history
    - Style guidelines
    """
    
    def generate(self, context: Dict[str, Any]) -> str:
        """
        Generate a standard prompt based on context.
        
        Args:
            context (Dict[str, Any]): Context information.
            
        Returns:
            str: The generated prompt.
        """
        submission = context["submission"]
        subreddit = context["subreddit"]
        comments = context["comments"]
        
        # Extract top comments for context
        comment_texts = []
        for comment in comments:
            author = comment["author"]
            body = comment["body"]
            score = comment["score"]
            comment_texts.append(f"Comment by {author} (Score: {score}):\n{body}")
        
        comment_context = "\n\n".join(comment_texts) if comment_texts else "No comments yet."
        
        # Generate the prompt
        prompt = f"""
You are writing a comment on a Reddit post in r/{subreddit["name"]}, which is about {subreddit["description"]}.

The post is:
Title: {submission["title"]}
Content: {submission["body"]}

Here are the top comments on this post so far:
{comment_context}

Write a helpful, informative comment that:
1. Feels natural and conversational, like a real human Redditor
2. Avoids overly formal or structured language
3. Might include some casual elements like contractions or colloquialisms
4. Addresses the post directly and provides value
5. Fits the tone and style of r/{subreddit["name"]}

Your comment should NOT:
- Start with phrases like "As an AI" or "Here's my response"
- Sound too perfect or polished
- Use bullet points or numbered lists unless absolutely necessary
- Exceed 1000 characters

Just write the comment text directly, without any additional formatting or explanation.
"""
        
        return prompt


class SubredditSpecificTemplate(PromptTemplate):
    """
    Subreddit-specific prompt template.
    
    This template adjusts the prompt based on the specific subreddit.
    """
    
    # Dictionary of subreddit-specific prompt adjustments
    SUBREDDIT_STYLES = {
        "testingground4bots": {
            "tone": "casual and experimental",
            "style": "straightforward and helpful",
            "special_instructions": "This is a testing subreddit, so you can be more casual and direct."
        },
        "askreddit": {
            "tone": "conversational and engaging",
            "style": "personal and anecdotal",
            "special_instructions": "Share a personal perspective or story if relevant."
        },
        "explainlikeimfive": {
            "tone": "friendly and accessible",
            "style": "simple without being condescending",
            "special_instructions": "Use analogies and simple explanations without technical jargon."
        },
        "programming": {
            "tone": "knowledgeable but approachable",
            "style": "technical but clear",
            "special_instructions": "Include code examples or technical details when appropriate."
        },
        # Add more subreddits as needed
    }
    
    # Default style for subreddits not in the dictionary
    DEFAULT_STYLE = {
        "tone": "friendly and helpful",
        "style": "conversational",
        "special_instructions": "Be relevant to the topic and provide value."
    }
    
    def generate(self, context: Dict[str, Any]) -> str:
        """
        Generate a subreddit-specific prompt based on context.
        
        Args:
            context (Dict[str, Any]): Context information.
            
        Returns:
            str: The generated prompt.
        """
        submission = context["submission"]
        subreddit = context["subreddit"]
        comments = context["comments"]
        
        # Get subreddit-specific style
        subreddit_name = subreddit["name"].lower()
        style = self.SUBREDDIT_STYLES.get(subreddit_name, self.DEFAULT_STYLE)
        
        # Extract top comments for context
        comment_texts = []
        for comment in comments:
            author = comment["author"]
            body = comment["body"]
            score = comment["score"]
            comment_texts.append(f"Comment by {author} (Score: {score}):\n{body}")
        
        comment_context = "\n\n".join(comment_texts) if comment_texts else "No comments yet."
        
        # Generate the prompt
        prompt = f"""
You are writing a comment on a Reddit post in r/{subreddit["name"]}, which is about {subreddit["description"]}.

The post is:
Title: {submission["title"]}
Content: {submission["body"]}

Here are the top comments on this post so far:
{comment_context}

For r/{subreddit["name"]}, you should adopt a {style["tone"]} tone and a {style["style"]} style.
{style["special_instructions"]}

Write a comment that:
1. Feels natural and conversational, like a real human Redditor
2. Avoids overly formal or structured language
3. Includes some casual elements like contractions or colloquialisms
4. Addresses the post directly and provides value
5. Fits the tone and style of r/{subreddit["name"]}

Your comment should NOT:
- Start with phrases like "As an AI" or "Here's my response"
- Sound too perfect or polished
- Use bullet points or numbered lists unless absolutely necessary
- Exceed 1000 characters

Just write the comment text directly, without any additional formatting or explanation.
"""
        
        return prompt


class TemplateSelector:
    """
    Selects an appropriate template based on context.
    """
    
    def __init__(self):
        """Initialize the template selector with available templates."""
        self.templates = {
            "standard": StandardPromptTemplate(),
            "subreddit_specific": SubredditSpecificTemplate(),
        }
    
    def select_template(self, context: Dict[str, Any]) -> PromptTemplate:
        """
        Select an appropriate template based on context.
        
        Args:
            context (Dict[str, Any]): Context information.
            
        Returns:
            PromptTemplate: The selected template.
        """
        subreddit_name = context["subreddit"]["name"].lower()
        
        # Use subreddit-specific template if available
        if subreddit_name in SubredditSpecificTemplate.SUBREDDIT_STYLES:
            return self.templates["subreddit_specific"]
        
        # Default to standard template
        return self.templates["standard"]


if __name__ == "__main__":
    # Example usage
    import json
    
    # Load example context from a file
    with open("example_context.json", "r") as f:
        context = json.load(f)
    
    # Select template
    selector = TemplateSelector()
    template = selector.select_template(context)
    
    # Generate prompt
    prompt = template.generate(context)
    
    print(prompt)
