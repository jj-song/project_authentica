#!/usr/bin/env python3
"""
Humanization package for Project Authentica.
Makes AI-generated comments more human-like by learning from real comments.
"""

from src.humanization.analyzer import CommentAnalyzer
from src.humanization.sampler import CommentSampler
from src.humanization.prompt_enhancer import enhance_prompt 