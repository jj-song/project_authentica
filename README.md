# Project Authentica

An advanced Reddit bot system that posts AI-generated comments using OpenAI's API with sophisticated context awareness and thread analysis capabilities.

## Overview

Project Authentica is a sophisticated Reddit bot that uses OpenAI's API to generate context-aware, human-like comments on Reddit posts. The system analyzes thread structure, conversation patterns, and post context to create appropriate and engaging responses.

Key features:
- Advanced thread analysis and conversation pattern detection
- Context-aware prompt engineering with multiple template types
- Dynamic response strategy selection based on thread characteristics
- Human-like variations in response style and tone
- Flexible scheduling for automated or one-time operation

## Architecture

The system follows this general workflow:
1. **Thread Selection**: Finds suitable Reddit threads to engage with
2. **Context Collection**: Gathers context from submission, subreddit, and comments
3. **Thread Analysis**: Analyzes conversation structure and patterns
4. **Strategy Selection**: Determines optimal response approach
5. **Template Selection**: Chooses appropriate template based on context
6. **Response Generation**: Generates human-like response using OpenAI API
7. **Posting**: Posts the response to Reddit

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
│       ├── analyzer.py     # Thread structure analysis
│       ├── conversation.py # Conversation flow analysis
│       └── strategies.py   # Response strategy determination
├── scripts/                # Utility scripts
├── docs/                   # Documentation
│   ├── scope.md            # Project scope document
│   └── testing_plan.md     # Testing strategy and plan
└── tests/                  # Unit tests
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
- Conversation depth and breadth
- Key topics and sentiment
- User engagement patterns
- Discussion hotspots

### Context Collection
The context collector gathers relevant information from multiple sources:
- Submission content and metadata
- Subreddit information and rules
- Comment history and patterns
- Temporal context (time of day, day of week)

### Response Strategies
Based on thread analysis, the system selects optimal response strategies:
- **Question Answerer**: Provides helpful answers to questions
- **Conversation Joiner**: Engages with ongoing discussions
- **Direct Reply**: Responds directly to the submission
- **Hotspot Engagement**: Participates in active discussion areas
- **Popular Comment**: Replies to comments with high engagement

### Template System
The template system selects appropriate prompt templates based on context:
- **Standard**: General-purpose template
- **Subreddit-specific**: Customized for particular subreddits
- **Persona-based**: Uses different personas for variety
- **Content-type**: Adapts to questions, discussions, or advice requests
- **Comment Reply**: Specialized for replying to comments

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

##### Utility Functions
- `--check-comment COMMENT_ID`: Check status and performance of a specific comment
- `--show-context SUBMISSION_ID`: Show context collected for a specific submission
- `--view-comments SUBMISSION_ID`: View comments on a specific submission

##### Debug Options
- `--dry-run`: Generate but do not post comments
- `--verbose`, `-v`: Enable verbose output
- `--debug`: Enable debug mode with additional logging

#### Examples

```bash
# Check the performance of a specific comment
python -m src.main --check-comment n2qwmuo --verbose

# Show the context collected for a submission
python -m src.main --show-context 1ly07mf

# Generate a comment but don't post it (dry run)
python -m src.main --once --subreddit askscience --dry-run --verbose

# Run the bot with scheduler, checking every 45 minutes
python -m src.main --schedule --subreddit formula1 --interval 45 --jitter 10
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

# Thread Analysis
ENABLE_THREAD_ANALYSIS=true
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
# Database operations
from src.utils.database_utils import get_db_connection, execute_query

# Error handling
from src.utils.error_utils import handle_exceptions, RedditAPIError

# Logging configuration
from src.utils.logging_utils import get_component_logger

# Reddit API operations
from src.utils.reddit_utils import check_shadowban, get_comment_by_id
```

### Adding New Templates

Create a new class in `src/context/templates.py` that inherits from `PromptTemplate`:

```python
class MyCustomTemplate(PromptTemplate):
    def generate(self, context: Dict[str, Any]) -> str:
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
# In the determine_strategy method
if some_condition:
    return {
        "type": "my_new_strategy",
        "reasoning": "This strategy works because...",
        "target_comment": target_comment,
        "prompt_enhancements": {
            "instruction": "Special instruction for this strategy",
            "style_guidance": "Style guidance specific to this strategy"
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
