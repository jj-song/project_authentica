#!/usr/bin/env python3
"""
Logging utilities for Project Authentica.
Provides centralized logging configuration and helper functions.
"""

import logging
import os
import sys
import json
from typing import Optional, Dict, Any
import datetime

def configure_logging(
    level: int = logging.INFO,
    log_to_file: bool = False,
    log_file: Optional[str] = None,
    component: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        level (int): Logging level (default: logging.INFO)
        log_to_file (bool): Whether to log to a file (default: False)
        log_file (Optional[str]): Path to log file (default: logs/authentica.log)
        component (Optional[str]): Component name for the logger (default: root logger)
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if logging to file
    if log_to_file:
        if log_file is None:
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "authentica.log")
        else:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
    
    # Get logger
    logger_name = component if component else "authentica"
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicate logging
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if requested
    if log_to_file and log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_with_context(logger: logging.Logger, level: int, message: str, context: Dict[str, Any]) -> None:
    """
    Log a message with additional context information.
    
    Args:
        logger (logging.Logger): Logger to use
        level (int): Logging level (e.g., logging.INFO)
        message (str): Log message
        context (Dict[str, Any]): Additional context information
    """
    # Format context as key-value pairs
    context_str = ", ".join(f"{k}={v}" for k, v in context.items())
    full_message = f"{message} | Context: {context_str}"
    
    logger.log(level, full_message)

def get_component_logger(component_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger for a specific component.
    
    Args:
        component_name (str): Name of the component
        level (int): Logging level (default: logging.INFO)
        
    Returns:
        logging.Logger: Logger for the component
    """
    logger = logging.getLogger(component_name)
    logger.setLevel(level)
    
    # Add a handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def log_llm_interaction(
    prompt: str,
    response: str,
    subreddit: str,
    strategy: str,
    template: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log LLM interaction with prompt and response for analysis.
    
    Args:
        prompt (str): The prompt sent to LLM
        response (str): The response received from LLM
        subreddit (str): Subreddit name
        strategy (str): Response strategy used
        template (str): Template used for prompt generation
        metadata (Optional[Dict[str, Any]]): Additional metadata
    """
    # Create logs/prompts directory if it doesn't exist
    log_dir = "logs/prompts"
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate timestamp-based filename (sanitize strategy for filename)
    timestamp = datetime.datetime.now()
    safe_strategy = str(strategy).replace('/', '_').replace(' ', '_')[:50]  # Limit length and sanitize
    filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{subreddit}_{safe_strategy}.json"
    log_file = os.path.join(log_dir, filename)
    
    # Calculate prompt metrics
    prompt_length = len(prompt)
    response_length = len(response)
    estimated_tokens = (prompt_length + response_length) // 4  # Rough token estimate
    
    # Create structured log entry
    log_entry = {
        "timestamp": timestamp.isoformat(),
        "subreddit": subreddit,
        "strategy": strategy,
        "template": template,
        "prompt": prompt,
        "response": response,
        "metrics": {
            "prompt_length_chars": prompt_length,
            "response_length_chars": response_length,
            "estimated_tokens": estimated_tokens
        },
        "metadata": metadata or {}
    }
    
    # Write to file
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        # Fallback to regular logging if file write fails
        logger = get_component_logger("prompt_logger")
        logger.error(f"Failed to write prompt log file: {e}")


def log_prompt_metrics(
    prompt: str,
    subreddit: str,
    strategy: str,
    template: str,
    logger: Optional[logging.Logger] = None
) -> Dict[str, int]:
    """
    Log prompt metrics and return metrics dictionary.
    
    Args:
        prompt (str): The prompt to analyze
        subreddit (str): Subreddit name
        strategy (str): Response strategy used
        template (str): Template used
        logger (Optional[logging.Logger]): Logger to use
        
    Returns:
        Dict[str, int]: Metrics about the prompt
    """
    if logger is None:
        logger = get_component_logger("prompt_metrics")
    
    # Calculate metrics
    prompt_length = len(prompt)
    line_count = prompt.count('\n') + 1
    estimated_tokens = prompt_length // 4  # Rough estimate
    
    metrics = {
        "length_chars": prompt_length,
        "line_count": line_count,
        "estimated_tokens": estimated_tokens
    }
    
    # Log metrics with context
    log_with_context(
        logger=logger,
        level=logging.INFO,
        message=f"Prompt metrics for {strategy} template",
        context={
            "subreddit": subreddit,
            "template": template,
            **metrics
        }
    )
    
    # Warn if prompt is very long
    if prompt_length > 2500:
        logger.warning(f"Prompt length ({prompt_length} chars) exceeds recommended threshold (2500 chars)")
    
    return metrics


def setup_prompt_logging(verbose: bool = False) -> logging.Logger:
    """
    Set up dedicated prompt logging.
    
    Args:
        verbose (bool): Whether to enable verbose logging
        
    Returns:
        logging.Logger: Configured prompt logger
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logs directory structure
    os.makedirs("logs/prompts", exist_ok=True)
    
    # Configure prompt-specific logger with file output
    prompt_logger = configure_logging(
        level=log_level,
        log_to_file=True,
        log_file="logs/prompts/prompt_metrics.log",
        component="prompt_system"
    )
    
    return prompt_logger