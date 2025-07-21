#!/usr/bin/env python3
"""
Personality Analyzer Module for Project Authentica.
Uses LLM analysis to understand subreddit communication patterns and personality traits.
"""

import json
import logging
import sqlite3
import time
from typing import Dict, List, Any, Optional

import openai
from openai import OpenAI

from src.config import init_configuration
from src.utils.error_utils import handle_exceptions
from src.utils.logging_utils import get_component_logger

# Configure logging
logger = get_component_logger("personality_analyzer")


class PersonalityAnalyzer:
    """
    Analyzes subreddit personality traits using GPT-3.5 Turbo for cost-effective analysis.
    
    This class provides methods for:
    1. Analyzing comment samples to extract personality traits
    2. Caching personality data in database for cost optimization
    3. Providing personality-based guidance for response generation
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize the PersonalityAnalyzer.
        
        Args:
            db_connection (sqlite3.Connection): Database connection for caching
        """
        self.db = db_connection
        self.config = init_configuration()
        
        # Initialize OpenAI client for GPT-3.5 Turbo
        self.client = OpenAI(api_key=self.config["openai"]["api_key"])
        
        # Ensure the database table exists
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Initialize the database table for storing personality analysis."""
        cursor = self.db.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subreddit_personalities (
            subreddit TEXT PRIMARY KEY,
            tone TEXT NOT NULL,
            formality_level REAL NOT NULL,
            judgment_style TEXT NOT NULL,
            empathy_level REAL NOT NULL,
            directness_level REAL NOT NULL,
            humor_usage REAL NOT NULL,
            advice_approach TEXT NOT NULL,
            questioning_pattern TEXT NOT NULL,
            agreement_tendency REAL NOT NULL,
            length_preference TEXT NOT NULL,
            structure_preference TEXT NOT NULL,
            raw_analysis TEXT NOT NULL,
            updated_at REAL NOT NULL,
            sample_count INTEGER NOT NULL
        )
        ''')
        
        self.db.commit()
        logger.info("Personality analysis database table initialized")
    
    @handle_exceptions
    def analyze_subreddit_personality(self, subreddit_name: str, sample_comments: List[Dict[str, Any]], 
                                    force_update: bool = False) -> Optional[Dict[str, Any]]:
        """
        Analyze subreddit personality using LLM analysis with caching.
        
        Args:
            subreddit_name (str): Name of the subreddit
            sample_comments (List[Dict[str, Any]]): Sample comments for analysis
            force_update (bool): Whether to force a new analysis
            
        Returns:
            Optional[Dict[str, Any]]: Personality analysis results
        """
        # Check if we have recent analysis (less than 30 days old)
        if not force_update:
            cached_personality = self._get_cached_personality(subreddit_name, max_age_days=30)
            if cached_personality:
                logger.info(f"Using cached personality analysis for r/{subreddit_name}")
                return cached_personality
        
        # Perform new analysis
        logger.info(f"Performing LLM-based personality analysis for r/{subreddit_name}")
        
        if not sample_comments or len(sample_comments) < 3:
            logger.warning(f"Insufficient sample comments for r/{subreddit_name} personality analysis")
            return None
        
        # Prepare comments for analysis
        formatted_comments = self._format_comments_for_analysis(sample_comments)
        
        # Generate analysis prompt
        analysis_prompt = self._create_analysis_prompt(subreddit_name, formatted_comments)
        
        try:
            # Call GPT-3.5 Turbo for analysis
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in analyzing online community communication patterns and personality traits."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=800
            )
            
            raw_analysis = response.choices[0].message.content.strip()
            logger.info(f"Received personality analysis for r/{subreddit_name}")
            
            # Parse the structured analysis
            personality_data = self._parse_analysis_response(raw_analysis)
            
            if personality_data:
                # Store in database
                self._store_personality_analysis(subreddit_name, personality_data, raw_analysis, len(sample_comments))
                logger.info(f"Stored personality analysis for r/{subreddit_name}")
                return personality_data
            else:
                logger.error(f"Failed to parse personality analysis for r/{subreddit_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error during LLM personality analysis for r/{subreddit_name}: {e}")
            return None
    
    def _format_comments_for_analysis(self, comments: List[Dict[str, Any]]) -> str:
        """
        Format comments for LLM analysis.
        
        Args:
            comments (List[Dict[str, Any]]): Sample comments
            
        Returns:
            str: Formatted comments text
        """
        formatted = []
        for i, comment in enumerate(comments[:10], 1):  # Limit to 10 comments for token efficiency
            # Truncate very long comments
            body = comment['body']
            if len(body) > 400:
                body = body[:397] + "..."
                
            formatted.append(f"Comment {i} (Score: {comment['score']}):\n{body}")
        
        return "\n\n".join(formatted)
    
    def _create_analysis_prompt(self, subreddit_name: str, formatted_comments: str) -> str:
        """
        Create the analysis prompt for GPT-3.5 Turbo.
        
        Args:
            subreddit_name (str): Name of the subreddit
            formatted_comments (str): Formatted comments for analysis
            
        Returns:
            str: Analysis prompt
        """
        return f"""Analyze the communication patterns and personality traits of the r/{subreddit_name} community based on these sample comments:

{formatted_comments}

Please analyze and provide a structured response with the following traits (respond in this exact format):

TONE: [Describe the overall tone - options: casual, formal, supportive, critical, humorous, serious, mixed]

FORMALITY_LEVEL: [Rate 0.0-1.0 where 0.0 = very informal, 1.0 = very formal]

JUDGMENT_STYLE: [How the community judges situations - options: harsh, balanced, lenient, situation-dependent]

EMPATHY_LEVEL: [Rate 0.0-1.0 where 0.0 = low empathy, 1.0 = high empathy]

DIRECTNESS_LEVEL: [Rate 0.0-1.0 where 0.0 = very indirect, 1.0 = very direct]

HUMOR_USAGE: [Rate 0.0-1.0 where 0.0 = no humor, 1.0 = heavy humor usage]

ADVICE_APPROACH: [How advice is given - options: direct-solutions, supportive-guidance, tough-love, analytical, personal-experience]

QUESTIONING_PATTERN: [How questions are used - options: frequent-clarifying, engagement-focused, rare, analytical]

AGREEMENT_TENDENCY: [Rate 0.0-1.0 where 0.0 = often disagrees, 1.0 = often agrees]

LENGTH_PREFERENCE: [Typical response length - options: brief, moderate, detailed, varies]

STRUCTURE_PREFERENCE: [Typical structure - options: paragraphs, single-block, lists, mixed]

Focus on patterns that would help someone write responses that naturally fit this community's communication style."""
    
    def _parse_analysis_response(self, raw_analysis: str) -> Optional[Dict[str, Any]]:
        """
        Parse the structured analysis response from GPT-3.5 Turbo.
        
        Args:
            raw_analysis (str): Raw analysis response
            
        Returns:
            Optional[Dict[str, Any]]: Parsed personality data
        """
        try:
            personality_data = {}
            
            # Parse each field from the response
            lines = raw_analysis.split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'tone':
                        personality_data['tone'] = value
                    elif key == 'formality_level':
                        try:
                            personality_data['formality_level'] = float(value)
                        except ValueError:
                            personality_data['formality_level'] = 0.5
                    elif key == 'judgment_style':
                        personality_data['judgment_style'] = value
                    elif key == 'empathy_level':
                        try:
                            personality_data['empathy_level'] = float(value)
                        except ValueError:
                            personality_data['empathy_level'] = 0.5
                    elif key == 'directness_level':
                        try:
                            personality_data['directness_level'] = float(value)
                        except ValueError:
                            personality_data['directness_level'] = 0.5
                    elif key == 'humor_usage':
                        try:
                            personality_data['humor_usage'] = float(value)
                        except ValueError:
                            personality_data['humor_usage'] = 0.3
                    elif key == 'advice_approach':
                        personality_data['advice_approach'] = value
                    elif key == 'questioning_pattern':
                        personality_data['questioning_pattern'] = value
                    elif key == 'agreement_tendency':
                        try:
                            personality_data['agreement_tendency'] = float(value)
                        except ValueError:
                            personality_data['agreement_tendency'] = 0.5
                    elif key == 'length_preference':
                        personality_data['length_preference'] = value
                    elif key == 'structure_preference':
                        personality_data['structure_preference'] = value
            
            # Validate that we got the essential fields
            required_fields = ['tone', 'formality_level', 'judgment_style', 'empathy_level', 'directness_level']
            if all(field in personality_data for field in required_fields):
                return personality_data
            else:
                logger.warning(f"Missing required fields in personality analysis: {required_fields}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing personality analysis response: {e}")
            return None
    
    def _store_personality_analysis(self, subreddit_name: str, personality_data: Dict[str, Any], 
                                  raw_analysis: str, sample_count: int) -> None:
        """
        Store personality analysis in the database.
        
        Args:
            subreddit_name (str): Name of the subreddit
            personality_data (Dict[str, Any]): Parsed personality data
            raw_analysis (str): Raw analysis response
            sample_count (int): Number of comments analyzed
        """
        cursor = self.db.cursor()
        current_time = time.time()
        
        cursor.execute('''
            INSERT OR REPLACE INTO subreddit_personalities
            (subreddit, tone, formality_level, judgment_style, empathy_level, directness_level,
             humor_usage, advice_approach, questioning_pattern, agreement_tendency, 
             length_preference, structure_preference, raw_analysis, updated_at, sample_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            subreddit_name,
            personality_data.get('tone', 'mixed'),
            personality_data.get('formality_level', 0.5),
            personality_data.get('judgment_style', 'balanced'),
            personality_data.get('empathy_level', 0.5),
            personality_data.get('directness_level', 0.5),
            personality_data.get('humor_usage', 0.3),
            personality_data.get('advice_approach', 'supportive-guidance'),
            personality_data.get('questioning_pattern', 'engagement-focused'),
            personality_data.get('agreement_tendency', 0.5),
            personality_data.get('length_preference', 'moderate'),
            personality_data.get('structure_preference', 'paragraphs'),
            raw_analysis,
            current_time,
            sample_count
        ))
        
        self.db.commit()
    
    def _get_cached_personality(self, subreddit_name: str, max_age_days: int = 30) -> Optional[Dict[str, Any]]:
        """
        Get cached personality analysis from database.
        
        Args:
            subreddit_name (str): Name of the subreddit
            max_age_days (int): Maximum age in days
            
        Returns:
            Optional[Dict[str, Any]]: Cached personality data
        """
        cursor = self.db.cursor()
        max_age_seconds = max_age_days * 24 * 3600
        
        cursor.execute('''
            SELECT tone, formality_level, judgment_style, empathy_level, directness_level,
                   humor_usage, advice_approach, questioning_pattern, agreement_tendency,
                   length_preference, structure_preference, updated_at, sample_count
            FROM subreddit_personalities
            WHERE subreddit = ? AND updated_at > ?
        ''', (subreddit_name, time.time() - max_age_seconds))
        
        row = cursor.fetchone()
        if row:
            return {
                'tone': row[0],
                'formality_level': row[1],
                'judgment_style': row[2],
                'empathy_level': row[3],
                'directness_level': row[4],
                'humor_usage': row[5],
                'advice_approach': row[6],
                'questioning_pattern': row[7],
                'agreement_tendency': row[8],
                'length_preference': row[9],
                'structure_preference': row[10],
                'updated_at': row[11],
                'sample_count': row[12]
            }
        
        return None
    
    def get_personality_guidance(self, subreddit_name: str) -> Dict[str, str]:
        """
        Get personality-based guidance for response generation.
        
        Args:
            subreddit_name (str): Name of the subreddit
            
        Returns:
            Dict[str, str]: Personality guidance for prompts
        """
        personality = self._get_cached_personality(subreddit_name)
        if not personality:
            return {
                'tone_guidance': 'Use a balanced, conversational tone.',
                'style_guidance': 'Write naturally and authentically.',
                'approach_guidance': 'Be helpful and relevant to the discussion.'
            }
        
        # Generate guidance based on personality traits
        tone_guidance = self._generate_tone_guidance(personality)
        style_guidance = self._generate_style_guidance(personality)
        approach_guidance = self._generate_approach_guidance(personality)
        
        return {
            'tone_guidance': tone_guidance,
            'style_guidance': style_guidance,
            'approach_guidance': approach_guidance
        }
    
    def _generate_tone_guidance(self, personality: Dict[str, Any]) -> str:
        """Generate tone guidance based on personality analysis."""
        tone = personality.get('tone', 'mixed')
        formality = personality.get('formality_level', 0.5)
        humor = personality.get('humor_usage', 0.3)
        
        guidance = f"Adopt a {tone} tone"
        
        if formality < 0.3:
            guidance += " with very casual, informal language"
        elif formality < 0.7:
            guidance += " with moderately casual language"
        else:
            guidance += " with more polished, formal language"
        
        if humor > 0.6:
            guidance += ". Include appropriate humor when it fits naturally"
        elif humor > 0.3:
            guidance += ". Light humor is acceptable when appropriate"
        else:
            guidance += ". Keep humor minimal and focus on substance"
        
        return guidance + "."
    
    def _generate_style_guidance(self, personality: Dict[str, Any]) -> str:
        """Generate style guidance based on personality analysis."""
        directness = personality.get('directness_level', 0.5)
        length_pref = personality.get('length_preference', 'moderate')
        structure_pref = personality.get('structure_preference', 'paragraphs')
        
        guidance = []
        
        if directness > 0.7:
            guidance.append("Be direct and straightforward")
        elif directness > 0.3:
            guidance.append("Balance directness with tactfulness")
        else:
            guidance.append("Use a more indirect, gentle approach")
        
        if length_pref == 'brief':
            guidance.append("keep responses concise")
        elif length_pref == 'detailed':
            guidance.append("provide thorough, detailed responses")
        else:
            guidance.append("aim for moderate length responses")
        
        if structure_pref == 'single-block':
            guidance.append("use single paragraph format")
        elif structure_pref == 'lists':
            guidance.append("bullet points or lists are acceptable")
        
        return ". ".join(guidance).capitalize() + "."
    
    def _generate_approach_guidance(self, personality: Dict[str, Any]) -> str:
        """Generate approach guidance based on personality analysis."""
        empathy = personality.get('empathy_level', 0.5)
        judgment = personality.get('judgment_style', 'balanced')
        advice_approach = personality.get('advice_approach', 'supportive-guidance')
        agreement = personality.get('agreement_tendency', 0.5)
        
        guidance = []
        
        if empathy > 0.7:
            guidance.append("Show high empathy and emotional understanding")
        elif empathy > 0.3:
            guidance.append("Balance empathy with practical advice")
        else:
            guidance.append("Focus on practical solutions over emotional support")
        
        if judgment == 'harsh':
            guidance.append("be willing to give tough, critical feedback")
        elif judgment == 'lenient':
            guidance.append("be understanding and give benefit of the doubt")
        else:
            guidance.append("provide balanced, fair judgments")
        
        if agreement < 0.3:
            guidance.append("don't hesitate to disagree when appropriate")
        elif agreement > 0.7:
            guidance.append("be generally supportive and agreeable")
        
        return ". ".join(guidance).capitalize() + "."


if __name__ == "__main__":
    # Example usage
    import os
    from src.database import get_db_connection
    from src.humanization.sampler import CommentSampler
    from src.config import get_reddit_instance
    
    # Set up connections
    reddit = get_reddit_instance(os.getenv("BOT_USERNAME", "my_first_bot"))
    db_conn = get_db_connection()
    
    # Create analyzer and sampler
    analyzer = PersonalityAnalyzer(db_conn)
    sampler = CommentSampler(reddit, db_conn)
    
    # Test with a subreddit
    subreddit_name = "advice"
    samples = sampler.collect_samples(subreddit_name, count=10)
    
    if samples:
        personality = analyzer.analyze_subreddit_personality(subreddit_name, samples)
        if personality:
            print(f"=== Personality Analysis for r/{subreddit_name} ===")
            print(f"Tone: {personality['tone']}")
            print(f"Formality Level: {personality['formality_level']}")
            print(f"Judgment Style: {personality['judgment_style']}")
            print(f"Empathy Level: {personality['empathy_level']}")
            
            guidance = analyzer.get_personality_guidance(subreddit_name)
            print("\n=== Generated Guidance ===")
            for key, value in guidance.items():
                print(f"{key}: {value}")
    
    # Clean up
    db_conn.close()