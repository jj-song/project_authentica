# Project Authentica

An advanced Reddit bot system that posts AI-generated comments using OpenAI's API with sophisticated context awareness and thread analysis capabilities.

## Overview

Project Authentica is a sophisticated Reddit bot that uses OpenAI's API to generate context-aware, human-like comments on Reddit posts. The system analyzes thread structure, conversation patterns, and post context to create appropriate and engaging responses.

Key features:
- **Advanced Thread Analysis**: Quality scoring and engagement potential ranking
- **Context-Aware Responses**: Dynamic comment length adaptation based on subreddit patterns
- **Representative Comment Sampling**: Collects 5 representative comments per subreddit for context
- **Response Strategy Selection**: Intelligent targeting for direct replies vs comment replies
- **Human-like Variations**: Multiple template types with natural language variations
- **Performance Tracking**: Comment performance monitoring and analytics
- **Flexible Scheduling**: Automated or one-time operation with configurable intervals

## Architecture

The system follows this general workflow:
1. **Thread Selection**: Finds suitable Reddit threads to engage with using quality scoring
2. **Context Collection**: Gathers context from submission, subreddit, and representative comments
3. **Thread Analysis**: Analyzes conversation structure, patterns, and engagement potential
4. **Strategy Selection**: Determines optimal response approach (direct reply, comment reply, etc.)
5. **Template Selection**: Chooses appropriate template with dynamic length adaptation
6. **Response Generation**: Orchestrated by ResponseGenerator using OpenAI API
7. **Posting**: Posts the response to Reddit with performance tracking

The **ResponseGenerator** class serves as the central orchestration layer, implementing a pipeline pattern that coordinates all components from context collection through response generation.

## Directory Structure

```
project_authentica/
├── src/                    # Source code
│   ├── agent.py            # KarmaAgent class for Reddit interactions
│   ├── config.py           # Configuration utilities
│   ├── database.py         # Database handling
│   ├── llm_handler.py      # OpenAI API integration
│   ├── main.py             # Main entry point with scheduler
│   ├── response_generator.py # Response generation orchestration
│   ├── utils/              # Utility functions
│   │   ├── database_utils.py # Database operations
│   │   ├── error_utils.py  # Error handling and exceptions
│   │   ├── logging_utils.py # Logging configuration
│   │   └── reddit_utils.py # Reddit API operations
│   ├── context/            # Context collection and templates
│   │   ├── collector.py    # Gathers context from Reddit
│   │   └── templates.py    # Prompt templates and variations
│   ├── humanization/       # Human-like response generation
│   │   ├── analyzer.py     # Analyzes text for humanization
│   │   ├── prompt_enhancer.py # Enhances prompts for human-like responses
│   │   └── sampler.py      # Samples different response styles
│   └── thread_analysis/    # Thread analysis components
│       ├── analyzer.py     # Thread structure and quality analysis
│       ├── conversation.py # Conversation flow analysis
│       └── strategies.py   # Response strategy determination
├── scripts/                # Utility scripts
│   ├── SCRIPTS_GUIDE.md    # Guide for utility scripts
│   ├── test_enhanced_prompts.py # Prompt testing utilities
│   └── test_thread_analysis.py  # Thread analysis testing
├── docs/                   # Documentation
│   ├── scope.md            # Project scope document
│   └── testing_plan.md     # Testing strategy and plan
├── tests/                  # Unit tests
│   ├── test_agent.py       # Agent functionality tests
│   ├── test_llm_handler.py # LLM handler tests
│   ├── test_thread_analysis.py # Thread analysis tests
│   └── test_utils.py       # Utility function tests
└── CLAUDE.md               # AI assistant context and development guide
```

## Features

### Phase 1: Basic Bot
- Reddit API integration using PRAW
- Scheduler for periodic posting
- Basic database for tracking posts
- Simple prompt engineering

### Phase 2: Context-Aware Responses
- Enhanced context collection (subreddit, post, temporal factors)
- Dynamic template system
- Improved prompt engineering
- Better database schema

### Phase 3: Human-like Variations
- Sophisticated prompt templates
- Natural language variations
- Persona-based responses
- Comment-to-comment reply functionality

### Phase 4: Advanced Thread Analysis
- Full thread ingestion and hierarchical comment forest analysis
- Conversation flow understanding with pattern detection
- Adaptive response strategies based on thread characteristics
- Integration with the existing prompt engineering system

### Phase 5: Code Structure Improvements
- Modular utility functions with clear separation of concerns
- Enhanced error handling and logging
- Improved database operations with connection pooling
- Standardized interfaces and method signatures

## Detailed Features

### Thread Analysis
The thread analysis module examines Reddit threads to understand conversation structure, patterns, and dynamics. It identifies:
- **Quality Scoring**: Ranks submissions by engagement potential using multiple factors
- **Conversation Depth and Breadth**: Analyzes comment tree structure and branching
- **Key Topics and Sentiment**: Extracts discussion themes and emotional tone
- **User Engagement Patterns**: Identifies active contributors and participation levels
- **Discussion Hotspots**: Locates areas of high activity for strategic engagement

### Context Collection
The context collector gathers relevant information from multiple sources:
- **Submission Analysis**: Content, metadata, and author information
- **Subreddit Profiling**: Community rules, description, and posting patterns
- **Representative Comments**: 5 high-quality comments that exemplify subreddit style
- **Comment Length Statistics**: Adaptive length constraints based on community norms
- **Temporal Context**: Time-based factors for optimal engagement timing
- **Enhanced Comment Context**: Deep analysis for comment-to-comment replies

### Response Strategies
Based on thread analysis, the system selects optimal response strategies:
- **Question Answerer**: Provides helpful answers to questions
- **Conversation Joiner**: Engages with ongoing discussions
- **Direct Reply**: Responds directly to the submission
- **Hotspot Engagement**: Participates in active discussion areas
- **Popular Comment**: Replies to comments with high engagement

### Template System
The template system selects appropriate prompt templates based on context:
- **Standard**: General-purpose template with dynamic length adaptation
- **Subreddit-specific**: Customized for particular communities with representative examples
- **Persona-based**: Multiple personas with distinct communication styles
- **Content-type**: Adapts to questions, discussions, advice, or technical content
- **Comment Reply**: Specialized templates for thoughtful comment-to-comment engagement
- **Variation Engine**: Applies 2+ random variations for natural language diversity

### Human-like Variations
To create more natural responses, the system applies variations to:
- Tone (casual, formal, humorous)
- Style (anecdotal, questioning, reflective)
- Language patterns (contractions, casual expressions)

## Usage

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/project_authentica.git
cd project_authentica
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your API keys and settings
```

### Running the Bot

Project Authentica provides a comprehensive command-line interface for all operations.

#### Basic Usage

```bash
# Run the bot once without scheduling
python -m src.main --once --subreddit AskReddit --limit 1

# Run with scheduler
python -m src.main --schedule --subreddit formula1 --interval 45
```

#### Available Commands and Options

##### Operation Modes
- `--once`: Run the bot once without scheduling
- `--schedule`: Run the bot with the scheduler (default)

##### Target Parameters
- `--subreddit`, `-s`: Subreddit to scan (default: formula1)
- `--limit`, `-l`: Maximum number of posts to process (default: 1)
- `--sort`: Sort method for posts (choices: hot, new, top, rising; default: hot)

##### Scheduler Options
- `--interval`: Minutes between scheduled runs (default: 30)
- `--jitter`: Random jitter in minutes to add to interval (default: 5)

##### Analysis and Debugging Utilities
- `--check-comment COMMENT_ID`: Check status and performance of a specific comment
- `--show-context SUBMISSION_ID`: Show context collected for a specific submission
- `--view-comments SUBMISSION_ID`: View comments on a specific submission with threading

##### Development and Testing Options
- `--dry-run`: Generate but do not post comments (shows generated content)
- `--verbose`, `-v`: Enable verbose output with detailed logging
- `--debug`: Enable debug mode with comprehensive diagnostic information

#### Examples

```bash
# Check the performance of a specific comment with detailed metrics
python -m src.main --check-comment n2qwmuo --verbose

# Show the complete context collection and strategy selection for a submission
python -m src.main --show-context 1ly07mf --verbose

# View all comments in a submission with thread analysis
python -m src.main --view-comments 1ly07mf --verbose

# Generate a comment but don't post it (shows full response generation pipeline)
python -m src.main --once --subreddit askscience --dry-run --verbose

# Run the bot with scheduler, checking every 45 minutes with 10-minute jitter
python -m src.main --schedule --subreddit formula1 --interval 45 --jitter 10

# Debug mode with comprehensive logging (useful for development)
python -m src.main --once --subreddit testingground4bots --debug --dry-run

# Process multiple posts from a specific subreddit with quality ranking
python -m src.main --once --subreddit SkincareAddiction --limit 5 --sort hot --verbose
```

## Configuration

Create a `.env` file with the following variables:
```
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# LLM Settings
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=250

# Feature Flags
ENABLE_THREAD_ANALYSIS=true
ENABLE_HUMANIZATION=true

# Runtime Settings
DRY_RUN=false
BOT_USERNAME=my_first_bot

# Thread Selection Settings
SKIP_STICKIED_POSTS=true
SKIP_META_POSTS=true
MIN_POST_QUALITY_SCORE=40
```

Create a `praw.ini` file with your Reddit API credentials:
```
[my_first_bot]
client_id=your_client_id
client_secret=your_client_secret
user_agent=python:project_authentica:v1.0 (by /u/YourUsername)
username=your_reddit_username
password=your_reddit_password
```

## Development

### Using Utility Modules

The project now uses specialized utility modules for common operations:

```python
# Response Generation (main orchestration)
from src.response_generator import ResponseGenerator

# Database operations
from src.utils.database_utils import get_db_connection, execute_query

# Error handling
from src.utils.error_utils import handle_exceptions, RedditAPIError

# Logging configuration
from src.utils.logging_utils import get_component_logger

# Reddit API operations
from src.utils.reddit_utils import check_shadowban, get_comment_by_id

# Context and template selection
from src.context.collector import ContextCollector
from src.context.templates import TemplateSelector, VariationEngine

# Thread analysis and strategies
from src.thread_analysis.analyzer import ThreadAnalyzer
from src.thread_analysis.strategies import ResponseStrategy
```

### Adding New Templates

Create a new class in `src/context/templates.py` that inherits from `PromptTemplate`:

```python
class MyCustomTemplate(PromptTemplate):
    def generate(self, context: Dict[str, Any]) -> str:
        # Access comment length statistics for adaptive sizing
        length_stats = context.get("comment_length_stats", {})
        target_length = length_stats.get("avg_length", 500)
        
        # Use representative comments for style guidance
        representative_comments = context.get("representative_comments", [])
        
        # Custom template generation logic
        return prompt_text
```

### Adding New Variations

Add new variation types to the `VariationEngine` class in `src/context/templates.py`:

```python
# Add to existing variation types
NEW_VARIATIONS = [
    "Be slightly more technical in your explanation.",
    "Use more descriptive language.",
]
```

### Adding New Response Strategies

Add new strategy types to the `ResponseStrategy` class in `src/thread_analysis/strategies.py`:

```python
# Add to StrategyType enum
class StrategyType(Enum):
    MY_NEW_STRATEGY = "my_new_strategy"
    # ... existing strategies

# In the determine_strategy method
if some_condition:
    return {
        "type": StrategyType.MY_NEW_STRATEGY.value,
        "reasoning": "This strategy works because...",
        "target_comment": target_comment,
        "prompt_enhancements": {
            "instruction": "Special instruction for this strategy",
            "style_guidance": "Style guidance specific to this strategy",
            "length_adjustment": "Adjust for community norms"
        }
    }
```

## Testing

The project includes comprehensive unit tests for all components. See `docs/testing_plan.md` for the complete testing strategy.

To run tests:
```bash
pytest
```

To run specific test modules:
```bash
pytest tests/test_agent.py
```

## Development Roadmap

### Completed
- ✅ Basic bot functionality with OpenAI integration
- ✅ Context-aware prompt engineering
- ✅ Advanced thread analysis
- ✅ Multiple response strategies
- ✅ Template system with variations
- ✅ Code structure cleanup and modularization

### In Progress
- 🔄 Human-like response improvements
- 🔄 Comprehensive testing suite

### Planned
- 📅 Performance tracking and analytics
- 📅 Multi-subreddit optimization
- 📅 Conversation memory and continuity
