#!/usr/bin/env python3
"""
Response Strategy module for Project Authentica.
Provides adaptive response strategies based on thread analysis.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Enumeration of response strategy types."""
    DIRECT_REPLY = "direct_reply"  # Reply directly to the submission
    POPULAR_COMMENT = "popular_comment"  # Reply to a popular comment
    CONVERSATION_JOINER = "conversation_joiner"  # Join an ongoing conversation
    HOTSPOT_ENGAGEMENT = "hotspot_engagement"  # Engage with a discussion hotspot
    INFORMATION_PROVIDER = "information_provider"  # Provide factual information
    QUESTION_ANSWERER = "question_answerer"  # Answer a question
    OPINION_SHARER = "opinion_sharer"  # Share an opinion
    CHAIN_EXTENDER = "chain_extender"  # Extend a conversation chain


class ResponseStrategy:
    """
    Generates adaptive response strategies based on thread analysis.
    
    This class provides methods for:
    1. Determining the best response strategy based on thread analysis
    2. Generating strategy-specific prompt enhancements
    3. Selecting optimal comment targets for replies
    4. Adapting to conversation dynamics
    """
    
    def __init__(self):
        """Initialize the ResponseStrategy generator."""
        self.strategy_weights = {
            StrategyType.DIRECT_REPLY: 0.4,
            StrategyType.POPULAR_COMMENT: 0.2,
            StrategyType.CONVERSATION_JOINER: 0.15,
            StrategyType.HOTSPOT_ENGAGEMENT: 0.15,
            StrategyType.INFORMATION_PROVIDER: 0.025,
            StrategyType.QUESTION_ANSWERER: 0.025,
            StrategyType.OPINION_SHARER: 0.025,
            StrategyType.CHAIN_EXTENDER: 0.025,
        }
    
    def determine_strategy(self, thread_analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the best response strategy based on thread analysis.
        
        Args:
            thread_analysis (Dict[str, Any]): Analysis of the thread.
            context (Dict[str, Any]): Context information about the submission.
            
        Returns:
            Dict[str, Any]: Selected strategy with details.
        """
        logger.info("Determining response strategy")
        
        # Adjust weights based on thread analysis
        adjusted_weights = self._adjust_weights(thread_analysis, context)
        
        # Select strategy based on adjusted weights
        selected_strategy = self._select_weighted_strategy(adjusted_weights)
        
        # Determine target comment (if applicable)
        target_comment = self._determine_target_comment(selected_strategy, thread_analysis, context)
        
        # Generate strategy-specific prompt enhancements
        prompt_enhancements = self._generate_prompt_enhancements(selected_strategy, target_comment, thread_analysis)
        
        strategy_details = {
            "type": selected_strategy.value,
            "target_comment": target_comment,
            "prompt_enhancements": prompt_enhancements,
            "reasoning": self._generate_strategy_reasoning(selected_strategy, thread_analysis),
        }
        
        logger.info(f"Selected strategy: {selected_strategy.value}")
        return strategy_details
    
    def _adjust_weights(self, thread_analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[StrategyType, float]:
        """
        Adjust strategy weights based on thread analysis.
        
        Args:
            thread_analysis (Dict[str, Any]): Analysis of the thread.
            context (Dict[str, Any]): Context information about the submission.
            
        Returns:
            Dict[StrategyType, float]: Adjusted strategy weights.
        """
        weights = self.strategy_weights.copy()
        
        # Adjust based on thread characteristics
        
        # If there are hotspots, increase hotspot engagement weight
        if thread_analysis.get("discussion_hotspots", []):
            weights[StrategyType.HOTSPOT_ENGAGEMENT] += 0.1
            weights[StrategyType.DIRECT_REPLY] -= 0.02
        
        # If there are long chains, increase chain extender weight
        if thread_analysis.get("max_chain_length", 0) > 3:
            weights[StrategyType.CHAIN_EXTENDER] += 0.1
            weights[StrategyType.DIRECT_REPLY] -= 0.02
        
        # If there are many back-and-forth conversations, increase conversation joiner weight
        if thread_analysis.get("reply_patterns", {}).get("back_and_forth", 0) > 2:
            weights[StrategyType.CONVERSATION_JOINER] += 0.1
            weights[StrategyType.DIRECT_REPLY] -= 0.02
        
        # If the submission is a question, increase question answerer weight
        submission = context.get("submission", {})
        title = submission.get("title", "").lower()
        body = submission.get("body", "").lower()
        if "?" in title or "?" in body or any(q in title for q in ["what", "how", "why", "when", "where", "who"]):
            weights[StrategyType.QUESTION_ANSWERER] += 0.2
            weights[StrategyType.OPINION_SHARER] -= 0.05
            weights[StrategyType.INFORMATION_PROVIDER] -= 0.05
        
        # If the submission is asking for opinions, increase opinion sharer weight
        if any(op in title for op in ["opinion", "think", "thoughts", "view", "perspective"]):
            weights[StrategyType.OPINION_SHARER] += 0.2
            weights[StrategyType.INFORMATION_PROVIDER] -= 0.1
        
        # If the submission is asking for information, increase information provider weight
        if any(info in title for info in ["info", "information", "explain", "details", "help"]):
            weights[StrategyType.INFORMATION_PROVIDER] += 0.2
            weights[StrategyType.OPINION_SHARER] -= 0.1
        
        # Normalize weights to sum to 1
        total_weight = sum(weights.values())
        if total_weight > 0:
            for strategy in weights:
                weights[strategy] /= total_weight
        
        return weights
    
    def _select_weighted_strategy(self, weights: Dict[StrategyType, float]) -> StrategyType:
        """
        Select a strategy based on weighted probabilities.
        
        Args:
            weights (Dict[StrategyType, float]): Strategy weights.
            
        Returns:
            StrategyType: Selected strategy.
        """
        strategies = list(weights.keys())
        probabilities = list(weights.values())
        
        return random.choices(strategies, weights=probabilities, k=1)[0]
    
    def _determine_target_comment(self, strategy: StrategyType, thread_analysis: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Determine the target comment for the selected strategy.
        
        Args:
            strategy (StrategyType): Selected strategy.
            thread_analysis (Dict[str, Any]): Analysis of the thread.
            context (Dict[str, Any]): Context information about the submission.
            
        Returns:
            Optional[Dict[str, Any]]: Target comment information, or None for direct replies.
        """
        if strategy == StrategyType.DIRECT_REPLY:
            return None
        
        # Get comments from context
        comments = context.get("comments", [])
        
        if not comments:
            return None
        
        if strategy == StrategyType.POPULAR_COMMENT:
            # Sort by score and select the highest
            sorted_comments = sorted(comments, key=lambda c: c.get("score", 0), reverse=True)
            if sorted_comments:
                return sorted_comments[0]
        
        elif strategy == StrategyType.HOTSPOT_ENGAGEMENT:
            # Use hotspots from thread analysis
            hotspots = thread_analysis.get("discussion_hotspots", [])
            if hotspots:
                hotspot = hotspots[0]
                # Find the corresponding comment in context
                for comment in comments:
                    if comment.get("id") == hotspot.get("comment_id"):
                        return comment
                # If not found, use the first comment
                return comments[0]
        
        elif strategy == StrategyType.CONVERSATION_JOINER:
            # Look for comments that are part of a conversation
            for comment in comments:
                if any(reply.get("author") != comment.get("author") for reply in comment.get("replies", [])):
                    return comment
            # If no conversation found, use a random comment
            return random.choice(comments)
        
        elif strategy == StrategyType.QUESTION_ANSWERER:
            # Look for comments with questions
            for comment in comments:
                if "?" in comment.get("body", ""):
                    return comment
            # If no question found, use a random comment
            return random.choice(comments)
        
        elif strategy == StrategyType.CHAIN_EXTENDER:
            # Use the end of a chain
            chains = thread_analysis.get("chains", [])
            if chains:
                longest_chain = max(chains, key=len)
                last_comment_id = longest_chain[-1]
                # Find the corresponding comment in context
                for comment in comments:
                    if comment.get("id") == last_comment_id:
                        return comment
        
        # Default to a random comment with positive score
        positive_comments = [c for c in comments if c.get("score", 0) > 0]
        if positive_comments:
            return random.choice(positive_comments)
        else:
            return random.choice(comments)
    
    def _generate_prompt_enhancements(self, strategy: StrategyType, target_comment: Optional[Dict[str, Any]], thread_analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate strategy-specific prompt enhancements.
        
        Args:
            strategy (StrategyType): Selected strategy.
            target_comment (Optional[Dict[str, Any]]): Target comment information.
            thread_analysis (Dict[str, Any]): Analysis of the thread.
            
        Returns:
            Dict[str, str]: Prompt enhancements for the strategy.
        """
        enhancements = {}
        
        # Common enhancements
        enhancements["context_note"] = f"This is a thread with {thread_analysis.get('comment_count', 0)} comments and a conversation density of {thread_analysis.get('conversation_density', 0):.2f}."
        
        # Strategy-specific enhancements
        if strategy == StrategyType.DIRECT_REPLY:
            enhancements["instruction"] = "Respond directly to the main post, addressing the key points raised by the original poster."
            enhancements["style_guidance"] = "Be comprehensive but concise, focusing on adding value to the discussion."
        
        elif strategy == StrategyType.POPULAR_COMMENT:
            if target_comment:
                enhancements["instruction"] = f"Respond to this popular comment by u/{target_comment.get('author', '[deleted]')}, which has a score of {target_comment.get('score', 0)}."
                enhancements["style_guidance"] = "Acknowledge the points made in the comment and build upon them with your own insights."
        
        elif strategy == StrategyType.CONVERSATION_JOINER:
            enhancements["instruction"] = "Join this ongoing conversation by addressing points made by multiple participants."
            enhancements["style_guidance"] = "Be conversational and reference previous points made in the discussion."
        
        elif strategy == StrategyType.HOTSPOT_ENGAGEMENT:
            enhancements["instruction"] = "Engage with this discussion hotspot that has generated significant interest."
            enhancements["style_guidance"] = "Add a fresh perspective or insight that contributes meaningfully to this active discussion point."
        
        elif strategy == StrategyType.INFORMATION_PROVIDER:
            enhancements["instruction"] = "Provide factual, informative content that adds value to the discussion."
            enhancements["style_guidance"] = "Be clear, accurate, and educational in your response, focusing on sharing knowledge."
        
        elif strategy == StrategyType.QUESTION_ANSWERER:
            if target_comment:
                question = self._extract_question(target_comment.get("body", ""))
                if question:
                    enhancements["instruction"] = f"Answer the question: '{question}'"
                else:
                    enhancements["instruction"] = "Answer the question posed in this comment."
            enhancements["style_guidance"] = "Be helpful and direct in your answer, providing clear information."
        
        elif strategy == StrategyType.OPINION_SHARER:
            enhancements["instruction"] = "Share your perspective or opinion on the topic being discussed."
            enhancements["style_guidance"] = "Be thoughtful and nuanced, acknowledging different viewpoints while expressing your own."
        
        elif strategy == StrategyType.CHAIN_EXTENDER:
            enhancements["instruction"] = "Continue this conversation chain by building on the previous comments."
            enhancements["style_guidance"] = "Maintain the flow and tone of the existing conversation while adding new insights."
        
        return enhancements
    
    def _extract_question(self, text: str) -> Optional[str]:
        """
        Extract a question from text.
        
        Args:
            text (str): Text to extract question from.
            
        Returns:
            Optional[str]: Extracted question or None.
        """
        # Simple question extraction (for demonstration)
        sentences = text.split('.')
        for sentence in sentences:
            if '?' in sentence:
                return sentence.strip() + '?'
        return None
    
    def _generate_strategy_reasoning(self, strategy: StrategyType, thread_analysis: Dict[str, Any]) -> str:
        """
        Generate reasoning for the selected strategy.
        
        Args:
            strategy (StrategyType): Selected strategy.
            thread_analysis (Dict[str, Any]): Analysis of the thread.
            
        Returns:
            str: Reasoning for the strategy selection.
        """
        if strategy == StrategyType.DIRECT_REPLY:
            return "Directly responding to the submission will provide value to the original poster and other readers."
        
        elif strategy == StrategyType.POPULAR_COMMENT:
            return "Replying to a popular comment increases visibility and engagement with your response."
        
        elif strategy == StrategyType.CONVERSATION_JOINER:
            return f"Joining an ongoing conversation with {thread_analysis.get('reply_patterns', {}).get('back_and_forth', 0)} back-and-forth exchanges will integrate your response into the discussion flow."
        
        elif strategy == StrategyType.HOTSPOT_ENGAGEMENT:
            return f"Engaging with a discussion hotspot that has {len(thread_analysis.get('discussion_hotspots', []))} active participants will maximize the impact of your contribution."
        
        elif strategy == StrategyType.INFORMATION_PROVIDER:
            return "Providing factual information will add educational value to the discussion."
        
        elif strategy == StrategyType.QUESTION_ANSWERER:
            return "Answering a specific question will directly help users seeking information."
        
        elif strategy == StrategyType.OPINION_SHARER:
            return "Sharing a thoughtful opinion will contribute to the diversity of perspectives in the discussion."
        
        elif strategy == StrategyType.CHAIN_EXTENDER:
            return f"Extending a conversation chain of length {thread_analysis.get('max_chain_length', 0)} will maintain the flow of discussion."
        
        return "This strategy was selected based on the thread analysis." 