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


class CommentReplyTemplate(PromptTemplate):
    """
    Template for generating replies to comments.
    
    This template is specifically designed for replying to existing comments
    rather than directly to the submission.
    """
    
    def generate(self, context: Dict[str, Any]) -> str:
        """
        Generate a prompt for replying to a comment.
        
        Args:
            context (Dict[str, Any]): Context information including the comment to reply to.
            
        Returns:
            str: The generated prompt.
        """
        submission = context["submission"]
        subreddit = context["subreddit"]
        comment_to_reply = context.get("comment_to_reply", {})
        
        if not comment_to_reply:
            # Fallback to standard template if no comment to reply to
            return StandardPromptTemplate().generate(context)
        
        # Extract comment information
        comment_author = comment_to_reply.get("author", "[deleted]")
        comment_body = comment_to_reply.get("body", "")
        
        # Generate the prompt
        prompt = f"""
You are replying to a comment on a Reddit post in r/{subreddit["name"]}.

The original post is:
Title: {submission["title"]}
Content: {submission["body"]}

You are specifically replying to this comment by u/{comment_author}:
"{comment_body}"

Write a natural, conversational reply that:
1. Directly addresses the specific points or questions in the comment
2. Maintains a friendly, helpful tone
3. Feels like a genuine human interaction
4. Adds value to the conversation
5. Fits the tone and style of r/{subreddit["name"]}

Your reply should NOT:
- Start with phrases like "As an AI" or "Here's my response"
- Sound too perfect or polished
- Use bullet points or numbered lists unless absolutely necessary
- Exceed 800 characters
- Repeat the same points already made in the comment

Just write the reply text directly, without any additional formatting or explanation.
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
        "Use a few contractions (e.g., don't, can't, I'm).",
        "Include a casual expression or two.",
        "Use a slightly more informal vocabulary.",
        "Include a brief aside in parentheses.",
        "Start a sentence with a conjunction occasionally (And, But, So).",
    ]
    
    @classmethod
    def get_random_variations(cls, count: int = 2) -> List[str]:
        """
        Get a list of random variations.
        
        Args:
            count (int): Number of variations to get.
            
        Returns:
            List[str]: List of variation instructions.
        """
        all_variations = cls.TONE_VARIATIONS + cls.STYLE_VARIATIONS + cls.LANGUAGE_VARIATIONS
        return random.sample(all_variations, min(count, len(all_variations)))
    
    @classmethod
    def apply_variations(cls, prompt: str, variation_count: int = 2) -> str:
        """
        Apply random variations to a prompt.
        
        Args:
            prompt (str): The base prompt.
            variation_count (int): Number of variations to apply.
            
        Returns:
            str: The prompt with variations applied.
        """
        # Get random variations
        variations = cls.get_random_variations(variation_count)
        
        # Add variations to the prompt
        variation_text = "\n\n".join(variations)
        
        if variation_text:
            prompt += f"\n\nAdditional style guidance:\n{variation_text}"
        
        return prompt


class TemplateSelector:
    """
    Selects the most appropriate template based on context.
    """
    
    def __init__(self):
        """
        Initialize the template selector with all available templates.
        """
        self.templates = {
            "standard": StandardPromptTemplate(),
            "subreddit_specific": SubredditSpecificTemplate(),
            "persona_based": PersonaBasedTemplate(),
            "content_type": ContentTypeTemplate(),
            "comment_reply": CommentReplyTemplate(),
        }
        
    def select_template(self, context: Dict[str, Any], comment_to_reply=None) -> PromptTemplate:
        """
        Select the most appropriate template based on context.
        
        Args:
            context (Dict[str, Any]): Context information.
            comment_to_reply: If provided, select the comment reply template.
            
        Returns:
            PromptTemplate: The selected template.
        """
        # If we're replying to a comment, use the comment reply template
        if comment_to_reply is not None:
            logger.info("Selected comment_reply template")
            return self.templates["comment_reply"]
            
        # Check if we have subreddit-specific information
        subreddit_name = context["subreddit"]["name"].lower()
        if subreddit_name in SubredditSpecificTemplate.SUBREDDIT_STYLES:
            logger.info(f"Selected subreddit_specific template for r/{subreddit_name}")
            return self.templates["subreddit_specific"]
        
        # Check if we can identify the content type
        submission = context["submission"]
        if ContentTypeTemplate.is_question(submission):
            logger.info("Selected content_type template for question")
            return self.templates["content_type"]
        elif ContentTypeTemplate.is_advice_request(submission):
            logger.info("Selected content_type template for advice request")
            return self.templates["content_type"]
        
        # Randomly select between standard and persona-based templates
        if random.random() < 0.7:  # 70% chance for persona-based
            logger.info("Selected persona_based template")
            return self.templates["persona_based"]
        else:
            logger.info("Selected standard template")
            return self.templates["standard"]
    
    def generate_with_variations(self, context: Dict[str, Any], variation_count: int = 2, comment_to_reply=None) -> str:
        """
        Generate a prompt with variations using the selected template.
        
        Args:
            context (Dict[str, Any]): Context information.
            variation_count (int): Number of variations to apply.
            comment_to_reply: If provided, generate a reply to this comment.
            
        Returns:
            str: The generated prompt with variations.
        """
        # Select the appropriate template
        template = self.select_template(context, comment_to_reply)
        
        # Generate the base prompt
        if comment_to_reply is not None:
            # Add the comment to reply to in the context
            context["comment_to_reply"] = {
                "id": comment_to_reply.id,
                "body": comment_to_reply.body,
                "author": str(comment_to_reply.author) if comment_to_reply.author else "[deleted]",
                "score": comment_to_reply.score,
            }
            
        base_prompt = template.generate(context)
        
        # Apply variations
        return VariationEngine.apply_variations(base_prompt, variation_count)


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
