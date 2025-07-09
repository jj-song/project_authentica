# Project Authentica

A sophisticated Reddit bot system that posts AI-generated comments using OpenAI's API.

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

## Architecture

The system consists of several components:

1. **Agent**: Main bot logic for selecting posts and scheduling
2. **Context Collector**: Gathers relevant context about posts
3. **Template System**: Dynamic templates for different scenarios
4. **Variation Engine**: Adds human-like variations to responses
5. **Thread Analyzer**: Analyzes conversation patterns and dynamics
6. **Response Strategist**: Determines optimal response approaches

## Usage

### Configuration

Create a `.env` file with:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
```

### Running the Bot

Regular scheduled operation:
```
python src/main.py
```

Single run for testing:
```
python scripts/run_once.py
```

Thread analysis testing:
```
python scripts/test_thread_analysis.py [submission_id]
```

## Development

### Adding New Templates

Create a new class in `src/context/templates.py` that inherits from `BasePromptTemplate`.

### Adding New Variations

Add new variation functions to the `VariationEngine` class in `src/context/templates.py`.

### Adding New Response Strategies

Add new strategy types to the `StrategyType` enum in `src/thread_analysis/strategies.py` and update the `ResponseStrategy` class.
