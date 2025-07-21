#!/usr/bin/env python3
"""
Prompt Enhancer Module for Project Authentica.
Enhances prompts with human-like examples and guidelines.
"""

import logging
import random
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def enhance_prompt(base_prompt: str, samples: List[Dict[str, Any]], profile: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Enhance a prompt with human-like examples and guidelines.
    
    Args:
        base_prompt (str): The original prompt
        samples (List[Dict[str, Any]]): Sample comments to use as examples
        profile (Dict[str, Any]): Subreddit profile with statistical data
        context (Dict[str, Any]): Current context information
        
    Returns:
        str: The enhanced prompt
    """
    # Extract key statistics from profile
    length_stats = _extract_length_stats(profile)
    informality_stats = _extract_informality_stats(profile)
    structure_stats = _extract_structure_stats(profile)
    
    # Format sample comments
    sample_comments_text = _format_sample_comments(samples, context)
    
    # Generate humanization instructions
    humanization_instructions = _generate_humanization_instructions(
        length_stats, informality_stats, structure_stats, context
    )
    
    # Add personality-based guidance if available
    personality_guidance = ""
    if "subreddit_personality" in context:
        personality_guidance = _generate_personality_guidance(context["subreddit_personality"])
    
    # Combine everything into an enhanced prompt - prioritize examples
    enhanced_prompt = f"""{base_prompt}

STUDY THESE REAL EXAMPLES FROM THIS COMMUNITY FIRST:
{sample_comments_text}

{humanization_instructions}

{personality_guidance}

Write as a regular community member. Be direct and natural. Don't be perfect or overly agreeable.
"""
    
    return enhanced_prompt


def _extract_length_stats(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract length statistics from a subreddit profile.
    
    Args:
        profile (Dict[str, Any]): Subreddit profile
        
    Returns:
        Dict[str, Any]: Length statistics
    """
    if not profile or 'length' not in profile:
        return {
            'char_mean': 200,
            'char_stdev': 50,
            'word_mean': 40,
            'word_stdev': 10,
            'sentence_mean': 3,
            'target_range': (50, 200)
        }
    
    length = profile['length']
    char_length = length.get('char_length', {})
    word_length = length.get('word_length', {})
    sentence_count = length.get('sentence_count', {})
    
    char_mean = char_length.get('mean', 200)
    char_stdev = char_length.get('stdev', 50)
    
    # Calculate a reasonable target range (mean ± 0.5 stdev)
    lower = max(25, int(char_mean - 0.5 * char_stdev))
    upper = max(100, int(char_mean + 0.5 * char_stdev))
    
    return {
        'char_mean': char_mean,
        'char_stdev': char_stdev,
        'word_mean': word_length.get('mean', 40),
        'word_stdev': word_length.get('stdev', 10),
        'sentence_mean': sentence_count.get('mean', 3),
        'target_range': (lower, upper)
    }


def _extract_informality_stats(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract informality statistics from a subreddit profile.
    
    Args:
        profile (Dict[str, Any]): Subreddit profile
        
    Returns:
        Dict[str, Any]: Informality statistics
    """
    if not profile or 'informality' not in profile:
        return {
            'informality_score': 0.5,
            'contraction_rate': 1.0,
            'emoji_rate': 0.2,
            'caps_rate': 0.1,
            'multi_punct_rate': 0.2,
            'abbrev_rate': 0.3
        }
    
    informality = profile['informality']
    
    return {
        'informality_score': informality.get('informality_score', 0.5),
        'contraction_rate': informality.get('contraction_rate', 1.0),
        'emoji_rate': informality.get('emoji_rate', 0.2),
        'caps_rate': informality.get('caps_rate', 0.1),
        'multi_punct_rate': informality.get('multi_punct_rate', 0.2),
        'abbrev_rate': informality.get('abbrev_rate', 0.3)
    }


def _extract_structure_stats(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structure statistics from a subreddit profile.
    
    Args:
        profile (Dict[str, Any]): Subreddit profile
        
    Returns:
        Dict[str, Any]: Structure statistics
    """
    if not profile or 'structure' not in profile:
        return {
            'paragraph_mean': 1.5,
            'has_bullets_ratio': 0.1,
            'has_quotes_ratio': 0.1,
            'has_links_ratio': 0.2
        }
    
    structure = profile['structure']
    paragraph_count = structure.get('paragraph_count', {})
    
    return {
        'paragraph_mean': paragraph_count.get('mean', 1.5),
        'has_bullets_ratio': structure.get('has_bullets_ratio', 0.1),
        'has_quotes_ratio': structure.get('has_quotes_ratio', 0.1),
        'has_links_ratio': structure.get('has_links_ratio', 0.2)
    }


def _generate_humanization_instructions(
    length_stats: Dict[str, Any],
    informality_stats: Dict[str, Any],
    structure_stats: Dict[str, Any],
    context: Dict[str, Any]
) -> str:
    """
    Generate instructions for humanizing the response.
    
    Args:
        length_stats (Dict[str, Any]): Length statistics
        informality_stats (Dict[str, Any]): Informality statistics
        structure_stats (Dict[str, Any]): Structure statistics
        context (Dict[str, Any]): Current context information
        
    Returns:
        str: Humanization instructions
    """
    # Determine if this is a reply or direct comment
    is_reply = 'comment_to_reply' in context
    comment_type = "reply" if is_reply else "comment"
    
    # Get length target range
    lower, upper = length_stats['target_range']
    
    # Generate structure guidance based on statistics
    structure_guidance = []
    if structure_stats['paragraph_mean'] < 1.2:
        structure_guidance.append("Use a single paragraph in most cases.")
    elif structure_stats['paragraph_mean'] < 2:
        structure_guidance.append("Use 1-2 short paragraphs.")
    else:
        structure_guidance.append(f"Use about {int(structure_stats['paragraph_mean'])} paragraphs.")
    
    if structure_stats['has_bullets_ratio'] < 0.05:
        structure_guidance.append("Avoid using bullet points or numbered lists.")
    
    # Generate informality guidance based on statistics
    informality_guidance = []
    if informality_stats['informality_score'] > 0.7:
        informality_guidance.append("Be casual and conversational.")
        if informality_stats['contraction_rate'] > 1.5:
            informality_guidance.append("Use plenty of contractions (don't, I'm, you're, etc.).")
    elif informality_stats['informality_score'] > 0.4:
        informality_guidance.append("Be moderately casual and natural.")
        if informality_stats['contraction_rate'] > 0.8:
            informality_guidance.append("Use some contractions (don't, I'm, you're, etc.).")
    else:
        informality_guidance.append("Maintain a somewhat formal but still conversational tone.")
    
    # Add imperfection instructions
    imperfection_guidance = [
        "Include at least one natural imperfection in your writing.",
        "This could be a slightly awkward phrasing, a minor grammatical quirk, or a casual sentence fragment."
    ]
    
    # Add specific instructions about usernames, emojis, agreeableness, and questions
    specific_guidance = [
        "DO NOT address the user by their username (don't use u/ or @ mentions).",
        "DO NOT use emojis in your response.",
        "Avoid overly perfect grammar and structure - real humans make small mistakes.",
        "DON'T be excessively agreeable or overly validating - it's okay to disagree or be neutral when warranted.",
        "IMPORTANT: DO NOT ask questions to drive engagement - most real Reddit comments make a statement and move on.",
        "AVOID multiple questions in one response - real users rarely ask 2+ questions in casual comments.",
        "DON'T sound like a therapist with excessive empathy statements or validation phrases."
    ]
    
    # Combine all guidance
    structure_text = " ".join(structure_guidance)
    informality_text = " ".join(informality_guidance)
    imperfection_text = " ".join(imperfection_guidance)
    specific_text = " ".join(specific_guidance)
    
    instructions = f"""
WRITING GUIDELINES:
- LENGTH: {lower}-{upper} characters typical for this subreddit
- STYLE: {informality_text} {structure_text}
- NATURAL IMPERFECTIONS: {imperfection_text}
- AVOID: AI phrases, usernames, emojis, excessive politeness, perfect grammar

CRITICAL RULES: {specific_text}
"""
    
    return instructions


def _format_sample_comments(samples: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
    """
    Format sample comments for inclusion in the prompt.
    
    Args:
        samples (List[Dict[str, Any]]): Sample comments
        context (Dict[str, Any]): Current context information
        
    Returns:
        str: Formatted sample comments text
    """
    if not samples:
        return "No examples available."
    
    formatted_samples = []
    for i, sample in enumerate(samples, 1):
        # Truncate very long comments
        body = sample['body']
        if len(body) > 300:
            body = body[:297] + "..."
        
        # Don't include username in the example label to avoid encouraging username mentions
        formatted_samples.append(f"EXAMPLE {i} (Score: {sample['score']}):\n{body}")
    
    examples_text = "\n\n".join(formatted_samples)
    
    # Add explicit instructions to study and mimic the examples
    study_instructions = "\nIMPORTANT: Study these examples. Notice their natural tone, length, casual imperfections, and straightforward style. Blend in naturally."
    
    return examples_text + "\n\n" + study_instructions


def _generate_personality_guidance(personality_data: Dict[str, Any]) -> str:
    """
    Generate personality-based guidance for prompt enhancement.
    
    Args:
        personality_data (Dict[str, Any]): Personality analysis data
        
    Returns:
        str: Personality guidance text
    """
    if not personality_data:
        return ""
    
    guidance_parts = []
    
    # Tone guidance
    tone = personality_data.get('tone', 'mixed')
    formality = personality_data.get('formality_level', 0.5)
    
    tone_instruction = f"COMMUNITY PERSONALITY: This community has a {tone} tone"
    if formality < 0.3:
        tone_instruction += " with very casual, informal communication"
    elif formality < 0.7:
        tone_instruction += " with moderately casual communication"
    else:
        tone_instruction += " with more polished, formal communication"
    guidance_parts.append(tone_instruction + ".")
    
    # Empathy and judgment guidance
    empathy = personality_data.get('empathy_level', 0.5)
    judgment = personality_data.get('judgment_style', 'balanced')
    
    if empathy > 0.7:
        guidance_parts.append("Show high empathy and emotional understanding in your response.")
    elif empathy < 0.3:
        guidance_parts.append("Focus on practical solutions rather than emotional support.")
    
    if judgment == 'harsh':
        guidance_parts.append("This community tends to give direct, critical feedback when warranted.")
    elif judgment == 'lenient':
        guidance_parts.append("This community tends to be understanding and give people the benefit of the doubt.")
    
    # Directness guidance
    directness = personality_data.get('directness_level', 0.5)
    if directness > 0.7:
        guidance_parts.append("Be direct and straightforward in your communication.")
    elif directness < 0.3:
        guidance_parts.append("Use a more tactful, indirect approach when addressing sensitive topics.")
    
    # Humor guidance
    humor = personality_data.get('humor_usage', 0.3)
    if humor > 0.6:
        guidance_parts.append("Light humor is common and acceptable when it fits naturally.")
    elif humor < 0.2:
        guidance_parts.append("Keep humor minimal and focus on substantive content.")
    
    # Agreement tendency
    agreement = personality_data.get('agreement_tendency', 0.5)
    if agreement < 0.3:
        guidance_parts.append("Don't hesitate to respectfully disagree when you have a different perspective.")
    elif agreement > 0.7:
        guidance_parts.append("This community tends to be supportive and agreeable in discussions.")
    
    if guidance_parts:
        return "COMMUNITY STYLE: " + " ".join(guidance_parts)
    
    return ""


if __name__ == "__main__":
    # Example usage
    import os
    import json
    from src.config import get_reddit_instance
    from src.database import get_db_connection
    from src.humanization.sampler import CommentSampler
    
    # Set up connections
    reddit = get_reddit_instance(os.getenv("BOT_USERNAME", "my_first_bot"))
    db_conn = get_db_connection()
    
    # Create sampler and get samples
    sampler = CommentSampler(reddit, db_conn)
    subreddit_name = "formula1"
    samples = sampler.get_representative_samples(subreddit_name, {}, count=2)
    profile = sampler.get_subreddit_profile(subreddit_name)
    
    # Create a test prompt
    test_prompt = "Write a comment responding to a post about Formula 1 racing."
    
    # Enhance the prompt
    enhanced = enhance_prompt(test_prompt, samples, profile, {})
    
    print("=== ENHANCED PROMPT ===")
    print(enhanced)
    
    # Clean up
    db_conn.close() 