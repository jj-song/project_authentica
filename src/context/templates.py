#!/usr/bin/env python3
"""
Prompt template module for Project Authentica.
Provides templates for generating prompts based on context.
"""

import random
import logging
from typing import Dict, Any, List, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


class PersonaBasedTemplate(PromptTemplate):
    """
    Persona-based prompt template.
    
    This template generates prompts based on different personas that can be assigned to the bot.
    """
    
    # Dictionary of personas
    PERSONAS = {
        "helpful_expert": {
            "description": "You are a knowledgeable expert in the subject matter, sharing insights in a helpful way.",
            "tone": "informative but approachable",
            "quirks": "Occasionally uses field-specific terminology but explains it well."
        },
        "casual_enthusiast": {
            "description": "You are an enthusiastic hobbyist who loves discussing this topic.",
            "tone": "excited and casual",
            "quirks": "Uses exclamation points and expresses genuine excitement. Shares personal anecdotes."
        },
        "thoughtful_advisor": {
            "description": "You are a thoughtful advisor who carefully considers all angles before responding.",
            "tone": "balanced and considerate",
            "quirks": "Often acknowledges multiple perspectives and nuances."
        },
        "friendly_neighbor": {
            "description": "You are like a friendly neighbor offering advice over the fence.",
            "tone": "warm and conversational",
            "quirks": "Uses folksy expressions and friendly language. Offers practical advice."
        },
        "curious_questioner": {
            "description": "You are someone who asks thoughtful questions while providing insights.",
            "tone": "inquisitive and engaging",
            "quirks": "Asks rhetorical questions. Encourages deeper thinking."
        }
    }
    
    def __init__(self, persona_key: Optional[str] = None):
        """
        Initialize the persona-based template.
        
        Args:
            persona_key (Optional[str]): The key for the persona to use.
                If None, a random persona will be selected.
        """
        self.persona_key = persona_key
    
    def generate(self, context: Dict[str, Any]) -> str:
        """
        Generate a persona-based prompt based on context.
        
        Args:
            context (Dict[str, Any]): Context information.
            
        Returns:
            str: The generated prompt.
        """
        submission = context["submission"]
        subreddit = context["subreddit"]
        comments = context["comments"]
        
        # Select persona - use specified one or choose randomly
        if self.persona_key and self.persona_key in self.PERSONAS:
            persona = self.PERSONAS[self.persona_key]
        else:
            persona_key = random.choice(list(self.PERSONAS.keys()))
            persona = self.PERSONAS[persona_key]
            logger.info(f"Randomly selected persona: {persona_key}")
        
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
{persona["description"]}

You are commenting on a Reddit post in r/{subreddit["name"]}, which is about {subreddit["description"]}.

The post is:
Title: {submission["title"]}
Content: {submission["body"]}

Here are the top comments on this post so far:
{comment_context}

Your tone should be {persona["tone"]}.
Personality quirk: {persona["quirks"]}

Write a comment that:
1. Feels natural and conversational, like a real human Redditor with the persona described
2. Avoids overly formal or structured language
3. Includes some casual elements like contractions or colloquialisms
4. Addresses the post directly and provides value
5. Fits the tone and style of your persona

Your comment should NOT:
- Start with phrases like "As an AI" or "Here's my response"
- Sound too perfect or polished
- Use bullet points or numbered lists unless absolutely necessary
- Exceed 1000 characters

Just write the comment text directly, without any additional formatting or explanation.
"""
        
        return prompt


class ContentTypeTemplate(PromptTemplate):
    """
    Content type-specific template.
    
    This template adjusts the prompt based on the type of content in the submission.
    """
    
    # Content type detection functions
    @staticmethod
    def is_question(submission: Dict[str, Any]) -> bool:
        """Check if the submission is a question."""
        title = submission["title"].lower()
        body = submission["body"].lower()
        
        # Check for question marks
        if "?" in title or "?" in body:
            return True
        
        # Check for question words
        question_words = ["who", "what", "when", "where", "why", "how", "can", "should", "could", "would", "is", "are", "do", "does", "did", "will"]
        for word in question_words:
            if title.startswith(word + " ") or body.startswith(word + " "):
                return True
        
        return False
    
    @staticmethod
    def is_discussion(submission: Dict[str, Any]) -> bool:
        """Check if the submission is a discussion starter."""
        title = submission["title"].lower()
        body = submission["body"].lower()
        
        discussion_phrases = [
            "what do you think", "thoughts on", "discuss", "opinion", "debate",
            "what's your take", "what are your thoughts", "let's talk about"
        ]
        
        for phrase in discussion_phrases:
            if phrase in title or phrase in body:
                return True
        
        return False
    
    @staticmethod
    def is_advice_request(submission: Dict[str, Any]) -> bool:
        """Check if the submission is requesting advice."""
        title = submission["title"].lower()
        body = submission["body"].lower()
        
        advice_phrases = [
            "advice", "help", "need help", "suggestion", "recommend", "what should i do",
            "how do i", "how can i", "tips", "guidance"
        ]
        
        for phrase in advice_phrases:
            if phrase in title or phrase in body:
                return True
        
        return False
    
    def generate(self, context: Dict[str, Any]) -> str:
        """
        Generate a content type-specific prompt based on context.
        
        Args:
            context (Dict[str, Any]): Context information.
            
        Returns:
            str: The generated prompt.
        """
        submission = context["submission"]
        subreddit = context["subreddit"]
        comments = context["comments"]
        
        # Determine content type
        content_type = "general"
        content_instructions = ""
        
        if self.is_question(submission):
            content_type = "question"
            content_instructions = "This is a question post. Provide a helpful, direct answer. Consider different perspectives if appropriate."
        elif self.is_discussion(submission):
            content_type = "discussion"
            content_instructions = "This is a discussion post. Share your thoughts and perspectives. Consider different angles and encourage further discussion."
        elif self.is_advice_request(submission):
            content_type = "advice"
            content_instructions = "This is an advice request. Offer helpful, practical advice based on the situation described. Be supportive and constructive."
        
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

Content type: {content_type}
{content_instructions}

Here are the top comments on this post so far:
{comment_context}

Write a helpful, informative comment that:
1. Feels natural and conversational, like a real human Redditor
2. Avoids overly formal or structured language
3. Might include some casual elements like contractions or colloquialisms
4. Addresses the post directly and provides value
5. Is appropriate for the content type ({content_type})

Your comment should NOT:
- Start with phrases like "As an AI" or "Here's my response"
- Sound too perfect or polished
- Use bullet points or numbered lists unless absolutely necessary
- Exceed 1000 characters

Just write the comment text directly, without any additional formatting or explanation.
"""
        
        return prompt


class VariationEngine:
    """
    Adds variations to prompts to create more diverse responses.
    """
    
    # Variation types
    TONE_VARIATIONS = [
        "Be slightly more casual than usual.",
        "Be a bit more formal but still conversational.",
        "Use a touch of humor where appropriate.",
        "Be especially supportive and empathetic.",
        "Be concise and to the point.",
        "Be thoughtful and reflective.",
    ]
    
    STYLE_VARIATIONS = [
        "Include a brief personal anecdote if relevant.",
        "Ask a thoughtful question at the end to encourage engagement.",
        "Start with a brief reaction to the post before diving into your response.",
        "Include a relevant analogy or metaphor if it helps explain your point.",
        "Acknowledge a point made in one of the existing comments.",
    ]
    
    LANGUAGE_VARIATIONS = [
        "Use more contractions than you normally would (e.g., 'I'd' instead of 'I would').",
        "Include 1-2 casual expressions or slang terms that fit the context.",
        "Use slightly more informal punctuation, like occasional '...' or '!'",
        "Vary your sentence length more than usual - mix short and long sentences.",
        "Use a few sentence fragments for emphasis. Just occasionally.",
    ]
    
    @classmethod
    def apply_variations(cls, prompt: str, variation_count: int = 2) -> str:
        """
        Apply random variations to a prompt.
        
        Args:
            prompt (str): The original prompt.
            variation_count (int): Number of variations to apply.
            
        Returns:
            str: The prompt with variations applied.
        """
        variations = []
        
        # Select random variations
        variations.extend(random.sample(cls.TONE_VARIATIONS, min(1, variation_count)))
        variations.extend(random.sample(cls.STYLE_VARIATIONS, min(1, variation_count)))
        
        if variation_count > 2:
            variations.extend(random.sample(cls.LANGUAGE_VARIATIONS, min(1, variation_count - 2)))
        
        # Shuffle the variations
        random.shuffle(variations)
        
        # Add variations to the prompt
        variation_text = "\n\nAdd these variations to your response:\n"
        for i, variation in enumerate(variations, 1):
            variation_text += f"{i}. {variation}\n"
        
        return prompt + variation_text


class TemplateSelector:
    """
    Selects an appropriate template based on context.
    """
    
    def __init__(self):
        """Initialize the template selector with available templates."""
        self.templates = {
            "standard": StandardPromptTemplate(),
            "subreddit_specific": SubredditSpecificTemplate(),
            "persona_based": PersonaBasedTemplate(),
            "content_type": ContentTypeTemplate(),
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
        submission = context["submission"]
        
        # Use content type template for questions and advice requests
        content_template = self.templates["content_type"]
        if content_template.is_question(submission) or content_template.is_advice_request(submission):
            logger.info(f"Selected content_type template for submission {submission['id']}")
            return content_template
        
        # Use subreddit-specific template if available
        if subreddit_name in SubredditSpecificTemplate.SUBREDDIT_STYLES:
            logger.info(f"Selected subreddit_specific template for r/{subreddit_name}")
            return self.templates["subreddit_specific"]
        
        # Randomly select between persona-based and standard templates
        if random.random() < 0.7:  # 70% chance for persona-based
            logger.info(f"Selected persona_based template (random)")
            return self.templates["persona_based"]
        
        # Default to standard template
        logger.info(f"Selected standard template (default)")
        return self.templates["standard"]
    
    def generate_with_variations(self, context: Dict[str, Any], variation_count: int = 2) -> str:
        """
        Generate a prompt with variations.
        
        Args:
            context (Dict[str, Any]): Context information.
            variation_count (int): Number of variations to apply.
            
        Returns:
            str: The generated prompt with variations.
        """
        # Select template
        template = self.select_template(context)
        
        # Generate base prompt
        prompt = template.generate(context)
        
        # Apply variations
        return VariationEngine.apply_variations(prompt, variation_count)


if __name__ == "__main__":
    # Example usage
    import json
    
    # Load example context from a file
    with open("example_context.json", "r") as f:
        context = json.load(f)
    
    # Select template
    selector = TemplateSelector()
    
    # Generate prompt with variations
    prompt = selector.generate_with_variations(context, variation_count=3)
    
    print(prompt)
