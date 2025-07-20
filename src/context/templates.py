#!/usr/bin/env python3
"""
Prompt template module for Project Authentica.
Provides templates for generating prompts based on context.
"""

import random
import logging
from typing import Dict, Any, List, Optional, Callable

from src.humanization.prompt_enhancer import enhance_prompt

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
        
        # Get comment length stats or use defaults
        length_stats = context.get("comment_length_stats", {"min_length": 50, "avg_length": 500, "max_length": 800})
        min_length = length_stats.get("min_length", 50)
        avg_length = length_stats.get("avg_length", 500)
        max_length = min(1000, int(avg_length * 1.2))
        
        # Generate a random target length between min and avg+20%
        target_length = int(min_length + (avg_length - min_length) * random.random())
        
        # Extract top comments for context
        comment_texts = []
        for comment in comments:
            author = comment["author"]
            body = comment["body"]
            score = comment["score"]
            comment_texts.append(f"Comment by {author} (Score: {score}):\n{body}")
        
        comment_context = "\n\n".join(comment_texts) if comment_texts else "No comments yet."
        
        # Add representative comments from the subreddit if available
        representative_comment_texts = []
        representative_comments = context.get("representative_comments", [])
        if representative_comments:
            representative_comment_texts.append("Here are some typical comments from this subreddit:")
            for i, comment in enumerate(representative_comments[:5]):  # Limit to 5 examples
                representative_comment_texts.append(f"Example {i+1} (Score: {comment['score']}):\n{comment['body']}")
        
        representative_comment_context = "\n\n".join(representative_comment_texts) if representative_comment_texts else ""
        
        # Generate the prompt
        prompt = f"""
You are writing a comment on a Reddit post in r/{subreddit["name"]}, which is about {subreddit["description"]}.

The post is:
Title: {submission["title"]}
Content: {submission["body"]}

Here are the top comments on this post so far:
{comment_context}
"""

        # Add representative comments if available
        if representative_comment_context:
            prompt += f"""

{representative_comment_context}
"""

        prompt += f"""
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
- Include usernames or direct references like "u/username"

Your comment should be between {min_length} and {max_length} characters (aim for natural flow rather than exact length).

Just write the comment text directly, without any additional formatting or explanation.
"""
        
        return prompt


class DirectSubmissionReplyTemplate(PromptTemplate):
    """
    Template for generating direct replies to submissions (top-level comments).
    
    This template is specifically designed for creating top-level comments
    that directly address the original post.
    """
    
    def generate(self, context: Dict[str, Any]) -> str:
        """
        Generate a prompt for replying directly to a submission.
        
        Args:
            context (Dict[str, Any]): Context information
            
        Returns:
            str: The generated prompt
        """
        submission = context["submission"]
        subreddit = context["subreddit"]
        comments = context["comments"]
        
        # Get comment length stats or use defaults
        length_stats = context.get("comment_length_stats", {"min_length": 50, "avg_length": 500, "max_length": 800})
        min_length = length_stats.get("min_length", 50)
        avg_length = length_stats.get("avg_length", 500)
        max_length = min(1000, int(avg_length * 1.2))
        
        # Generate a random target length between min and avg+20%
        target_length = int(min_length + (avg_length - min_length) * random.random())
        
        # Extract top comments for context
        comment_texts = []
        for comment in comments[:3]:  # Limit to top 3 comments for brevity
            author = comment["author"]
            body = comment["body"]
            score = comment["score"]
            comment_texts.append(f"Comment (Score: {score}):\n{body}")
        
        comment_context = "\n\n".join(comment_texts) if comment_texts else "No comments yet."
        
        # Add representative comments from the subreddit if available
        representative_comment_texts = []
        representative_comments = context.get("representative_comments", [])
        if representative_comments:
            representative_comment_texts.append("Here are some typical comments from this subreddit:")
            for i, comment in enumerate(representative_comments[:5]):  # Limit to 5 examples
                representative_comment_texts.append(f"Example {i+1} (Score: {comment['score']}):\n{comment['body']}")
        
        representative_comment_context = "\n\n".join(representative_comment_texts) if representative_comment_texts else ""
        
        # Generate the prompt
        prompt = f"""
You are writing a top-level comment on a Reddit post in r/{subreddit["name"]}.

The post is:
Title: {submission["title"]}
Content: {submission["body"]}

Some existing comments for context:
{comment_context}
"""

        # Add representative comments if available
        if representative_comment_context:
            prompt += f"""

{representative_comment_context}
"""

        prompt += f"""
Write a helpful, informative comment that:
1. Directly addresses the original post
2. Feels natural and conversational, like a real human Redditor
3. Avoids overly formal or structured language
4. Adds value to the conversation
5. Fits the tone and style of r/{subreddit["name"]}

Your comment should NOT:
- Start with phrases like "As an AI" or "Here's my response"
- Sound too perfect or polished
- Use bullet points or numbered lists unless absolutely necessary
- Include usernames or direct references like "u/username"

Your comment should be between {min_length} and {max_length} characters (aim for natural flow rather than exact length).

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
        
        # Get comment length stats or use defaults
        length_stats = context.get("comment_length_stats", {"min_length": 50, "avg_length": 500, "max_length": 800})
        min_length = length_stats.get("min_length", 50)
        avg_length = length_stats.get("avg_length", 500)
        max_length = min(1000, int(avg_length * 1.2))
        
        # Generate a random target length between min and avg+20%
        target_length = int(min_length + (avg_length - min_length) * random.random())
        
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
        
        # Add representative comments from the subreddit if available
        representative_comment_texts = []
        representative_comments = context.get("representative_comments", [])
        if representative_comments:
            representative_comment_texts.append("Here are some typical comments from this subreddit:")
            for i, comment in enumerate(representative_comments[:5]):  # Limit to 5 examples
                representative_comment_texts.append(f"Example {i+1} (Score: {comment['score']}):\n{comment['body']}")
        
        representative_comment_context = "\n\n".join(representative_comment_texts) if representative_comment_texts else ""
        
        # Generate the prompt
        prompt = f"""
You are writing a comment on a Reddit post in r/{subreddit["name"]}, which is about {subreddit["description"]}.

The post is:
Title: {submission["title"]}
Content: {submission["body"]}

Here are the top comments on this post so far:
{comment_context}
"""

        # Add representative comments if available
        if representative_comment_context:
            prompt += f"""

{representative_comment_context}
"""

        prompt += f"""
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
- Include usernames or direct references like "u/username"

Your comment should be between {min_length} and {max_length} characters (aim for natural flow rather than exact length).

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
            "description": "You are knowledgeable about the subject matter, sharing insights in a helpful way.",
            "tone": "informative but approachable",
            "quirks": "Occasionally uses field-specific terminology but explains it clearly."
        },
        "casual_enthusiast": {
            "description": "You are interested in this topic and enjoy discussing it.",
            "tone": "casual and conversational",
            "quirks": "Sometimes shares relevant personal experiences when appropriate."
        },
        "thoughtful_advisor": {
            "description": "You consider different angles before responding.",
            "tone": "balanced and considerate",
            "quirks": "Acknowledges different perspectives in the discussion."
        },
        "friendly_neighbor": {
            "description": "You're like someone offering advice over the fence.",
            "tone": "warm and conversational",
            "quirks": "Uses straightforward language and offers practical advice."
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
        
        # Get comment length stats or use defaults
        length_stats = context.get("comment_length_stats", {"min_length": 50, "avg_length": 500, "max_length": 800})
        min_length = length_stats.get("min_length", 50)
        avg_length = length_stats.get("avg_length", 500)
        max_length = min(1000, int(avg_length * 1.2))
        
        # Generate a random target length between min and avg+20%
        target_length = int(min_length + (avg_length - min_length) * random.random())
        
        # Select a random persona if none provided
        persona_key = self.persona_key
        if persona_key is None or persona_key not in self.PERSONAS:
            persona_key = random.choice(list(self.PERSONAS.keys()))
            
        persona = self.PERSONAS[persona_key]
        
        # Extract top comments for context
        comment_texts = []
        for comment in comments:
            author = comment["author"]
            body = comment["body"]
            score = comment["score"]
            comment_texts.append(f"Comment by {author} (Score: {score}):\n{body}")
        
        comment_context = "\n\n".join(comment_texts) if comment_texts else "No comments yet."
        
        # Add representative comments from the subreddit if available
        representative_comment_texts = []
        representative_comments = context.get("representative_comments", [])
        if representative_comments:
            representative_comment_texts.append("Here are some typical comments from this subreddit:")
            for i, comment in enumerate(representative_comments[:5]):  # Limit to 5 examples
                representative_comment_texts.append(f"Example {i+1} (Score: {comment['score']}):\n{comment['body']}")
        
        representative_comment_context = "\n\n".join(representative_comment_texts) if representative_comment_texts else ""
        
        # Generate the prompt
        prompt = f"""
{persona["description"]}

You are writing a comment on a Reddit post in r/{subreddit["name"]}, which is about {subreddit["description"]}.

The post is:
Title: {submission["title"]}
Content: {submission["body"]}

Here are the top comments on this post so far:
{comment_context}
"""

        # Add representative comments if available
        if representative_comment_context:
            prompt += f"""

{representative_comment_context}
"""

        prompt += f"""
Write a comment with a {persona["tone"]} tone.
{persona["quirks"]}

Your comment should:
1. Feels natural and conversational, like a real human Redditor
2. Avoids overly formal or structured language
3. Might include some casual elements like contractions or colloquialisms
4. Addresses the post directly and provides value
5. Fits the tone and style of r/{subreddit["name"]}

Your comment should NOT:
- Start with phrases like "As an AI" or "Here's my response"
- Sound too perfect or polished
- Use bullet points or numbered lists unless absolutely necessary
- Include usernames or direct references like "u/username"

Your comment should be between {min_length} and {max_length} characters (aim for natural flow rather than exact length).

Just write the comment text directly, without any additional formatting or explanation.
"""
        
        return prompt


class ContentTypeTemplate(PromptTemplate):
    """
    Content-type prompt template.
    
    This template adjusts the prompt based on the content type (question, discussion, advice).
    """
    
    @staticmethod
    def is_question(submission: Dict[str, Any]) -> bool:
        """
        Determine if a submission is a question.
        
        Args:
            submission (Dict[str, Any]): Submission information.
            
        Returns:
            bool: True if the submission is a question.
        """
        title = submission["title"].lower()
        body = submission["body"].lower()
        
        # Check for question marks
        if "?" in title or "?" in body:
            return True
        
        # Check for common question words
        question_words = ["what", "how", "why", "when", "where", "who", "which"]
        for word in question_words:
            if f"{word} " in title or f"{word} " in body:
                return True
        
        return False
    
    @staticmethod
    def is_discussion(submission: Dict[str, Any]) -> bool:
        """
        Determine if a submission is a discussion topic.
        
        Args:
            submission (Dict[str, Any]): Submission information.
            
        Returns:
            bool: True if the submission is a discussion topic.
        """
        title = submission["title"].lower()
        body = submission["body"].lower()
        
        # Check for common discussion indicators
        discussion_words = ["discussion", "debate", "thoughts", "opinions", "what do you think"]
        for word in discussion_words:
            if word in title or word in body:
                return True
        
        return False
    
    @staticmethod
    def is_advice_request(submission: Dict[str, Any]) -> bool:
        """
        Determine if a submission is an advice request.
        
        Args:
            submission (Dict[str, Any]): Submission information.
            
        Returns:
            bool: True if the submission is an advice request.
        """
        title = submission["title"].lower()
        body = submission["body"].lower()
        
        # Check for common advice request indicators
        advice_words = ["advice", "help", "suggestion", "recommend", "should i", "what should"]
        for word in advice_words:
            if word in title or word in body:
                return True
        
        return False
    
    def generate(self, context: Dict[str, Any]) -> str:
        """
        Generate a content-type specific prompt based on context.
        
        Args:
            context (Dict[str, Any]): Context information.
            
        Returns:
            str: The generated prompt.
        """
        submission = context["submission"]
        subreddit = context["subreddit"]
        comments = context["comments"]
        
        # Get comment length stats or use defaults
        length_stats = context.get("comment_length_stats", {"min_length": 50, "avg_length": 500, "max_length": 800})
        min_length = length_stats.get("min_length", 50)
        avg_length = length_stats.get("avg_length", 500)
        max_length = min(1000, int(avg_length * 1.2))
        
        # Generate a random target length between min and avg+20%
        target_length = int(min_length + (avg_length - min_length) * random.random())
        
        # Determine content type
        content_type = "general"
        content_instructions = ""
        
        if self.is_question(submission):
            content_type = "question"
            content_instructions = "Answer the question directly and provide helpful information. Consider different perspectives."
        elif self.is_advice_request(submission):
            content_type = "advice"
            content_instructions = "Provide thoughtful advice that considers the specific situation. Be supportive but realistic."
        elif self.is_discussion(submission):
            content_type = "discussion"
            content_instructions = "Contribute to the discussion with your own perspective or additional information. Encourage further conversation."
        else:
            content_type = "general"
            content_instructions = "Respond in a way that adds value to the conversation and is relevant to the post."
        
        # Extract top comments for context
        comment_texts = []
        for comment in comments:
            author = comment["author"]
            body = comment["body"]
            score = comment["score"]
            comment_texts.append(f"Comment by {author} (Score: {score}):\n{body}")
        
        comment_context = "\n\n".join(comment_texts) if comment_texts else "No comments yet."
        
        # Add representative comments from the subreddit if available
        representative_comment_texts = []
        representative_comments = context.get("representative_comments", [])
        if representative_comments:
            representative_comment_texts.append("Here are some typical comments from this subreddit:")
            for i, comment in enumerate(representative_comments[:5]):  # Limit to 5 examples
                representative_comment_texts.append(f"Example {i+1} (Score: {comment['score']}):\n{comment['body']}")
        
        representative_comment_context = "\n\n".join(representative_comment_texts) if representative_comment_texts else ""
        
        # Generate the prompt
        prompt = f"""
You are writing a comment on a Reddit post in r/{subreddit["name"]}.

The post is:
Title: {submission["title"]}
Content: {submission["body"]}

Content type: {content_type}
{content_instructions}

Here are the top comments on this post so far:
{comment_context}
"""

        # Add representative comments if available
        if representative_comment_context:
            prompt += f"""

{representative_comment_context}
"""

        prompt += f"""
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
- Include usernames or direct references like "u/username"

Your comment should be between {min_length} and {max_length} characters (aim for natural flow rather than exact length).

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
            # Fallback to direct submission reply template if no comment to reply to
            return DirectSubmissionReplyTemplate().generate(context)
        
        # Get comment length stats or use defaults
        length_stats = context.get("comment_length_stats", {"min_length": 50, "avg_length": 500, "max_length": 800})
        min_length = length_stats.get("min_length", 50)
        avg_length = length_stats.get("avg_length", 500)
        max_length = min(1000, int(avg_length * 1.2))
        
        # Generate a random target length between min and avg+20%
        target_length = int(min_length + (avg_length - min_length) * random.random())
        
        # Extract comment information
        comment_author = comment_to_reply.get("author", "[deleted]")
        comment_body = comment_to_reply.get("body", "")
        is_op = comment_to_reply.get("is_op", False)
        
        # Get the comment context analysis
        comment_analysis = comment_to_reply.get("context_analysis", {})
        is_top_level = comment_analysis.get("is_top_level", True)
        addresses_original = comment_analysis.get("addresses_original_content", False)
        
        # Create the relationship context instruction
        if is_top_level:
            relationship_instruction = "This comment is a direct reply to the original post."
        else:
            relationship_instruction = "This comment is part of a conversation thread, not a direct reply to the original post."
        
        if addresses_original:
            relationship_instruction += " It directly addresses content from the original post."
        
        if is_op:
            author_context = "This comment was written by the original poster."
        else:
            author_context = "This comment was written by someone other than the original poster."
        
        # Add representative comments from the subreddit if available
        representative_comment_texts = []
        representative_comments = context.get("representative_comments", [])
        if representative_comments:
            representative_comment_texts.append("Here are some typical comments from this subreddit:")
            for i, comment in enumerate(representative_comments[:5]):  # Limit to 5 examples for replies
                representative_comment_texts.append(f"Example {i+1} (Score: {comment['score']}):\n{comment['body']}")
        
        representative_comment_context = "\n\n".join(representative_comment_texts) if representative_comment_texts else ""
        
        # Generate the prompt
        prompt = f"""
You are replying to a comment on a Reddit post in r/{subreddit["name"]}.

The original post is:
Title: {submission["title"]}
Content: {submission["body"]}

{relationship_instruction}
{author_context}

Be aware of the relationship between the comment and the original post, but focus primarily on responding to the specific comment.

You are specifically replying to this comment:
"{comment_body}"
"""

        # Add representative comments if available
        if representative_comment_context:
            prompt += f"""

{representative_comment_context}
"""

        prompt += f"""
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
- Repeat the same points already made in the comment
- Include usernames or direct references like "u/username"

Your comment should be between {min_length} and {max_length} characters (aim for natural flow rather than exact length).

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
    
    LENGTH_VARIATIONS = [
        "Keep your response brief and to the point.",
        "Feel free to elaborate a bit more on your main point.",
        "Prioritize clarity over length in your response.",
        "Be succinct but thorough.",
    ]
    
    @classmethod
    def get_random_variations(cls, count: int = 2, include_length: bool = True) -> List[str]:
        """
        Get a list of random variations.
        
        Args:
            count (int): Number of variations to get.
            include_length (bool): Whether to include length variations.
            
        Returns:
            List[str]: List of variation instructions.
        """
        all_variations = cls.TONE_VARIATIONS + cls.STYLE_VARIATIONS + cls.LANGUAGE_VARIATIONS
        
        # Maybe include a length variation
        if include_length and random.random() < 0.3:  # 30% chance
            all_variations += cls.LENGTH_VARIATIONS
            
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
            "direct_submission_reply": DirectSubmissionReplyTemplate(),
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
        # If replying directly to a submission (no comment)
        if comment_to_reply is None:
            logger.info("Selected direct_submission_reply template")
            return self.templates["direct_submission_reply"]
        
        # If replying to a comment
        if comment_to_reply is not None:
            logger.info("Selected comment_reply template")
            return self.templates["comment_reply"]
        
        # Default to standard template as a fallback
        logger.info("Selected standard template (fallback)")
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
        base_prompt = template.generate(context)
        
        # Apply response strategy enhancements if available
        if "response_strategy" in context:
            strategy = context["response_strategy"]
            enhancements = strategy.get("prompt_enhancements", {})
            
            # Add strategy-specific instructions
            if "instruction" in enhancements:
                base_prompt += f"\n\nSpecific instruction: {enhancements['instruction']}"
            
            # Add style guidance
            if "style_guidance" in enhancements:
                base_prompt += f"\n\nStyle guidance: {enhancements['style_guidance']}"
            
            # Add context note
            if "context_note" in enhancements:
                base_prompt += f"\n\nAdditional context: {enhancements['context_note']}"
        
        # Apply humanization enhancements using prompt enhancer
        representative_comments = context.get("representative_comments", [])
        if representative_comments:
            try:
                # Create a simplified profile from context for the enhancer
                subreddit_profile = {
                    "length": {"char_length": {"mean": context.get("comment_length_stats", {}).get("avg_length", 300)}},
                    "informality": {"informality_score": 0.6},  # Default moderate informality
                    "structure": {"paragraph_count": {"mean": 1.5}}
                }
                
                # Enhance the prompt with humanization features
                base_prompt = enhance_prompt(base_prompt, representative_comments, subreddit_profile, context)
                logger.info("Applied humanization enhancements to prompt")
            except Exception as e:
                logger.warning(f"Failed to apply humanization enhancements: {e}")
        
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
