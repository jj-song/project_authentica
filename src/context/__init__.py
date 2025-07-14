#!/usr/bin/env python3
"""
Context Package for Project Authentica.
Provides tools for collecting and processing context information for prompt engineering.
"""

from src.context.collector import ContextCollector
from src.context.templates import (
    TemplateSelector, 
    PromptTemplate,
    StandardPromptTemplate,
    SubredditSpecificTemplate,
    PersonaBasedTemplate,
    ContentTypeTemplate,
    CommentReplyTemplate
)

__all__ = [
    'ContextCollector',
    'TemplateSelector',
    'PromptTemplate',
    'StandardPromptTemplate',
    'SubredditSpecificTemplate',
    'PersonaBasedTemplate',
    'ContentTypeTemplate',
    'CommentReplyTemplate'
]
