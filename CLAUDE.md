# Project Authentica - AI Assistant Context

## Project Summary

Project Authentica is a sophisticated Reddit bot system that generates AI-powered comments using OpenAI's API. The system features advanced thread analysis, context-aware response generation, and intelligent comment targeting to create engaging, human-like interactions on Reddit.

## Key Components

### Core Architecture
- **ResponseGenerator** (`src/response_generator.py`): Central orchestration layer coordinating the 5-stage pipeline with integrated LLM calling and comprehensive logging
- **KarmaAgent** (`src/agent.py`): Manages Reddit interactions, posting, and performance tracking
- **ThreadAnalyzer** (`src/thread_analysis/analyzer.py`): Analyzes thread structure and ranks submissions by quality
- **ContextCollector** (`src/context/collector.py`): Gathers submission, subreddit, and representative comment data with personality analysis integration
- **TemplateSelector** (`src/context/templates.py`): Selects and generates optimized prompts with dynamic length adaptation (35-50% length reduction)
- **PersonalityAnalyzer** (`src/humanization/personality_analyzer.py`): LLM-based subreddit personality analysis using GPT-3.5 Turbo with 30-day database caching

### Utility Modules
- **Database Utils** (`src/utils/database_utils.py`): Centralized database operations with connection pooling
- **Reddit Utils** (`src/utils/reddit_utils.py`): Reddit API operations including shadowban detection
- **Error Utils** (`src/utils/error_utils.py`): Standardized error handling and custom exceptions
- **Logging Utils** (`src/utils/logging_utils.py`): Component-specific logging configuration with comprehensive LLM interaction logging and structured JSON output

### Configuration
- **Environment Variables**: Defined in `src/config.py` with validation and defaults
- **Reddit Auth**: Managed through `praw.ini` configuration file
- **Feature Flags**: `ENABLE_THREAD_ANALYSIS`, `ENABLE_HUMANIZATION`, etc.
- **Database Schema**: Enhanced with `subreddit_personalities` table for personality analysis caching
- **Logging Infrastructure**: Automatic LLM interaction logging to `logs/prompts/` with structured JSON format

## Architecture Flow

1. **Thread Selection**: ThreadAnalyzer ranks submissions by engagement potential
2. **Context Collection**: ContextCollector gathers submission, subreddit, and representative comments with personality analysis integration
3. **Thread Analysis**: Detailed analysis of comment structure, patterns, and hotspots
4. **Strategy Selection**: ResponseStrategy determines optimal approach (direct reply vs comment reply)
5. **Template Selection**: TemplateSelector chooses optimized template with dynamic length adaptation and personality-based guidance
6. **Response Generation**: ResponseGenerator orchestrates LLM call with comprehensive prompt logging and metrics tracking
7. **Posting**: KarmaAgent posts comment and tracks performance

### Enhanced Features
- **Personality Analysis**: Automated GPT-3.5 Turbo analysis of subreddit communication patterns with 11 personality dimensions
- **Prompt Optimization**: 35-50% reduction in prompt length through duplicate removal, content consolidation, and example truncation
- **Comprehensive Logging**: Structured JSON logging of all LLM interactions with prompt metrics and performance tracking

## Development Commands

### Running the Bot
```bash
# Single run with dry-run mode for testing
python -m src.main --once --subreddit testingground4bots --dry-run --verbose

# Scheduled operation
python -m src.main --schedule --subreddit formula1 --interval 30 --jitter 5

# Debug mode with comprehensive logging and prompt analysis
python -m src.main --once --subreddit askscience --debug --dry-run
```

### LLM and Prompt Analysis
```bash
# View detailed prompt logs and metrics
ls logs/prompts/
cat logs/prompts/20250720_173612_Advice_*.json

# Monitor prompt optimization results
grep "Prompt metrics" logs/prompts/prompt_metrics.log
```

### Analysis and Debugging
```bash
# Check comment performance
python -m src.main --check-comment [COMMENT_ID] --verbose

# Analyze context collection for a submission
python -m src.main --show-context [SUBMISSION_ID] --verbose

# View thread structure and comments
python -m src.main --view-comments [SUBMISSION_ID] --verbose
```

### Testing
```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_agent.py
pytest tests/test_thread_analysis.py

# Run with coverage
pytest --cov=src
```

## Code Patterns

### Error Handling
- Use `@handle_exceptions` decorator for automatic error logging
- Custom exceptions in `src/utils/error_utils.py`
- Component-specific loggers from `get_component_logger()`

### Database Operations
- Always use `ensure_bot_registered()` before database operations
- Use connection pooling through `DatabaseManager` class
- Transactions for multi-step operations

### Response Generation
- Use `ResponseGenerator` for all response workflows
- Context collection includes representative comments and length statistics
- Strategy selection determines target (submission vs specific comment)
- Template generation includes variations for natural language diversity

### Configuration Access
```python
from src.config import init_configuration
config = init_configuration()

# Access OpenAI settings
api_key = config["openai"]["api_key"]
model = config["openai"]["model"]

# Check feature flags
if config["features"]["thread_analysis"]:
    # Use thread analysis
```

## Key Features

### Dynamic Length Adaptation
- Analyzes subreddit comment patterns to determine appropriate response length
- Uses representative comments to match community style
- Generates target length between min and average for natural variation
- Enhanced with personality-based length preferences from automated subreddit analysis

### Personality-Based Response Guidance
- **11 Personality Dimensions**: Tone, formality level, judgment style, empathy level, directness level, humor usage, advice approach, questioning pattern, agreement tendency, length preference, and structure preference
- **GPT-3.5 Turbo Analysis**: Cost-effective personality analysis with 30-day database caching
- **Automated Style Matching**: Dynamic response guidance based on subreddit communication patterns
- **Database Persistence**: Personality profiles stored in `subreddit_personalities` table with automatic updates

### Quality Scoring
- ThreadAnalyzer ranks submissions using multiple engagement factors
- Considers score, comment count, age, and discussion activity
- Prioritizes high-potential threads for better engagement

### Intelligent Comment Targeting
- Analyzes comment forest structure for optimal reply targets
- Selects from top 3 eligible comments based on score and substance
- Fallback to submission reply if no suitable comments found

### Representative Comment Sampling
- Collects 5 high-quality comments per subreddit for style reference
- Uses in prompt generation to match community voice and tone
- Updates context with community-specific examples
- Integrated with personality analysis for comprehensive style profiling
- Optimized placement in prompts to eliminate duplication and reduce token usage

## Debugging Guide

### Common Issues

1. **Authentication Errors**: Check `praw.ini` configuration and Reddit account status
2. **Database Errors**: Ensure bot is registered with `ensure_bot_registered()`
3. **API Limits**: Monitor OpenAI API usage and implement rate limiting
4. **Context Collection Failures**: Check Reddit API connectivity and subreddit access

### Logging Levels
- **INFO**: Normal operation, workflow stages
- **DEBUG**: Detailed analysis, strategy selection reasoning
- **ERROR**: Failures, exceptions, API errors
- **WARNING**: Recoverable issues, fallback actions

### LLM Interaction Logging
- **Structured JSON Output**: Complete LLM interactions logged to `logs/prompts/` directory
- **Prompt Metrics**: Character count, line count, and estimated token usage
- **Performance Tracking**: Response generation timing and success rates
- **Analysis Support**: Detailed logs for prompt optimization and debugging
- **Filename Sanitization**: Safe filename generation with timestamp and metadata

### Performance Monitoring
- Comment performance tracked in `comment_performance` table
- Action logging in `actions_log` table with detailed status
- Use `--check-comment` to analyze individual comment metrics

## Context for AI Assistants

### When Working on This Codebase
1. **Always use ResponseGenerator** for response generation workflows instead of calling LLM handler directly
2. **Follow the pipeline pattern**: Context → Analysis → Strategy → Template → Generation
3. **Include representative comments** in context collection for style matching
4. **Use quality scoring** when selecting threads for engagement
5. **Implement proper error handling** with component loggers and custom exceptions

### Key Files to Understand
- `src/main.py`: Entry point and CLI interface
- `src/response_generator.py`: Central orchestration logic with integrated LLM calling and logging
- `src/thread_analysis/strategies.py`: Strategy selection algorithms
- `src/context/templates.py`: Optimized template system with 35-50% length reduction
- `src/agent.py`: Reddit interaction and posting logic
- `src/humanization/personality_analyzer.py`: GPT-3.5 Turbo personality analysis with database caching
- `src/utils/logging_utils.py`: Comprehensive LLM interaction logging and prompt metrics

### Testing Strategy
- Mock Reddit and OpenAI APIs in tests
- Use fixtures for common test data (submissions, comments, contexts)
- Test each pipeline stage independently
- Include integration tests for end-to-end workflows

### Configuration Management
- Environment variables for API keys and feature flags
- `praw.ini` for Reddit authentication
- Runtime configuration through CLI arguments
- Validation and defaults in `src/config.py`

This codebase implements a sophisticated, multi-stage approach to automated Reddit engagement with emphasis on quality, context-awareness, and natural human-like interaction patterns.