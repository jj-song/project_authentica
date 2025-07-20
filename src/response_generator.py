#!/usr/bin/env python3
"""
Response Generator module for Project Authentica.
Orchestrates the flow from thread analysis to response generation.
"""

import logging
from typing import Dict, Any, Optional, List
import praw
from praw.models import Submission, Comment

from src.context.collector import ContextCollector
from src.thread_analysis.analyzer import ThreadAnalyzer
from src.thread_analysis.strategies import ResponseStrategy
from src.context.templates import TemplateSelector
from src.utils.logging_utils import get_component_logger, log_llm_interaction, log_prompt_metrics
from src.utils.error_utils import handle_exceptions


class ResponseGenerator:
    """
    Orchestrates the flow from thread analysis to response generation.
    
    This class implements a pipeline pattern with clear stages:
    1. Context Collection: Gather all relevant context information
    2. Thread Analysis: Analyze the thread structure and dynamics
    3. Strategy Selection: Determine the best response strategy
    4. Template Selection: Select the appropriate template based on context and strategy
    5. Response Generation: Generate the final response
    """
    
    def __init__(self, reddit_instance: praw.Reddit):
        """
        Initialize the ResponseGenerator.
        
        Args:
            reddit_instance (praw.Reddit): An authenticated Reddit instance.
        """
        self.reddit = reddit_instance
        self.logger = get_component_logger("ResponseGenerator")
        
        # Initialize components
        self.context_collector = ContextCollector(reddit_instance)
        self.thread_analyzer = ThreadAnalyzer(reddit_instance)
        self.strategy_selector = ResponseStrategy()
        self.template_selector = TemplateSelector()
        
        self.logger.info("ResponseGenerator initialized")
    
    @handle_exceptions
    def generate_response(self, 
                         submission: Submission, 
                         comment_to_reply: Optional[Comment] = None,
                         variation_count: int = 2,
                         verbose: bool = False) -> Dict[str, Any]:
        """
        Generate a response for a submission or comment.
        
        Args:
            submission (Submission): The Reddit submission
            comment_to_reply (Optional[Comment]): If provided, generate a reply to this comment
            variation_count (int): Number of variations to apply
            verbose (bool): Whether to log detailed information
            
        Returns:
            Dict[str, Any]: Response data including the generated text and metadata
        """
        self.logger.info(f"Generating response for submission {submission.id}")
        if comment_to_reply:
            self.logger.info(f"Target is comment {comment_to_reply.id}")
        
        # Step 1: Collect context
        self.logger.info("Collecting context...")
        context = self.context_collector.collect_context(submission)
        if verbose:
            self.logger.info(f"Collected context for submission '{submission.title}'")
        
        # Step 2: Analyze thread
        self.logger.info("Analyzing thread...")
        thread_analysis = self.thread_analyzer.analyze_thread(submission)
        if verbose:
            self.logger.info(f"Thread analysis complete: {len(thread_analysis.get('comment_forest', {}))} comments analyzed")
        
        # Step 3: Determine response strategy
        self.logger.info("Determining response strategy...")
        response_strategy = self.strategy_selector.determine_strategy(thread_analysis, context)
        if verbose:
            self.logger.info(f"Selected strategy: {response_strategy['type']}")
            self.logger.info(f"Strategy reasoning: {response_strategy['reasoning']}")
        
        # Step 4: Select template
        self.logger.info("Selecting template...")
        template = self.template_selector.select_template(response_strategy, context)
        if verbose:
            self.logger.info(f"Selected template: {template.__class__.__name__}")
        
        # If we have a target comment from the strategy and no explicit comment was provided
        target_comment = comment_to_reply
        if not target_comment and response_strategy.get('target_comment'):
            # Find the comment in the submission
            comment_id = response_strategy['target_comment'].get('id')
            if comment_id:
                for comment in submission.comments.list():
                    if hasattr(comment, "id") and comment.id == comment_id:
                        target_comment = comment
                        break
        
        # Add the comment to reply to in the context if needed
        if target_comment:
            # Get enhanced comment analysis
            comment_context = self.context_collector.analyze_comment_context(submission, target_comment)
            
            context["comment_to_reply"] = {
                "id": target_comment.id,
                "body": target_comment.body,
                "author": str(target_comment.author) if target_comment.author else "[deleted]",
                "score": target_comment.score,
                "is_op": target_comment.is_submitter,
                "context_analysis": comment_context
            }
        
        # Step 5: Generate response prompt
        self.logger.info("Generating response prompt...")
        prompt = self.template_selector.generate_with_variations(context, variation_count, target_comment)
        
        # Step 6: Call LLM to generate final response
        self.logger.info("Calling LLM for final response generation...")
        from src.llm_handler import call_openai_api, clean_response
        
        # Log prompt metrics
        subreddit_name = submission.subreddit.display_name
        strategy_name = getattr(response_strategy, 'strategy', getattr(response_strategy, 'type', str(response_strategy)))
        template_name = template.__class__.__name__
        
        prompt_metrics = log_prompt_metrics(
            prompt=prompt,
            subreddit=subreddit_name,
            strategy=strategy_name,
            template=template_name,
            logger=self.logger
        )
        
        raw_response = call_openai_api(prompt, verbose)
        response_text = clean_response(raw_response)
        
        # Log the complete LLM interaction
        log_llm_interaction(
            prompt=prompt,
            response=response_text,
            subreddit=subreddit_name,
            strategy=strategy_name,
            template=template_name,
            metadata={
                "submission_id": submission.id,
                "comment_id": target_comment.id if target_comment else None,
                "verbose": verbose,
                **prompt_metrics
            }
        )
        
        # Create response data
        response_data = {
            "text": response_text,
            "submission_id": submission.id,
            "comment_id": target_comment.id if target_comment else None,
            "strategy": response_strategy,
            "template": template.__class__.__name__,
            "context": context if verbose else None,  # Only include full context if verbose
        }
        
        self.logger.info("Response generation complete")
        return response_data 