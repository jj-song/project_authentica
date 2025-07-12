#!/usr/bin/env python3
"""
Logging utilities for Project Authentica.
Provides centralized logging configuration and helper functions.
"""

import logging
import os
import sys
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