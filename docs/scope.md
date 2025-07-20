# Project Authentica Scope Document

## Project Overview

Project Authentica is a Reddit bot system that posts AI-generated comments. The system is designed to scan specified subreddits, identify relevant posts, generate contextually appropriate comments using OpenAI's API, and post these comments to build karma. All actions are logged in a database for tracking and analysis.

## System Components

### 1. Database Management (`src/database.py` and `src/utils/database_utils.py`)

The database component handles all database interactions using SQLite. It maintains three main tables:
- `bots`: Stores information about registered bots
- `actions_log`: Logs all bot actions
- `comment_performance`: Tracks the performance of posted comments

**Current TODOs:**
- ✅ Implement comment performance tracking functionality
- Add database migration capabilities for schema updates
- Implement database backup functionality
- Add query functions for analytics and reporting

**Completed Improvements:**
- ✅ Fixed foreign key constraint failures with `ensure_bot_registered`
- ✅ Added `DatabaseManager` class with connection pooling
- ✅ Standardized database operations with proper error handling
- ✅ Added transaction management

### 2. Configuration Management (`src/config.py`)

The configuration component handles Reddit API authentication via praw.ini and environment variables.

**Current TODOs:**
- Implement configuration validation
- Add support for multiple bot configurations
- Create a configuration UI or CLI tool
- Implement secure credential rotation

### 3. Utility Functions (`src/utils/`)

Utility functions have been refactored into specialized modules:
- `database_utils.py`: Centralized database operations
- `reddit_utils.py`: Reddit API operations including `check_shadowban`
- `error_utils.py`: Standardized error handling and custom exceptions
- `logging_utils.py`: Centralized logging configuration

**Current TODOs:**
- Add rate limiting and throttling utilities
- Implement additional Reddit API utilities
- Add caching mechanisms for API responses

**Completed Improvements:**
- ✅ Expanded utility functions for common operations
- ✅ Added comprehensive error handling
- ✅ Implemented logging utilities
- ✅ Standardized method signatures and return types

### 4. LLM Handler (`src/llm_handler.py`)

Manages interactions with OpenAI's API to generate comments.

**Current TODOs:**
- Add support for different LLM providers (Claude, Llama, etc.)
- Implement caching for similar prompts
- Add content filtering and safety measures
- Optimize token usage

**Completed Improvements:**
- ✅ Implemented context-aware comment generation with dynamic length adaptation
- ✅ Added representative comment sampling for style matching
- ✅ Integrated with ResponseGenerator for orchestrated workflow
- ✅ Enhanced prompt engineering with variation engine
- ✅ Added comment-to-comment reply capabilities

### 5. Agent (`src/agent.py`)

The KarmaAgent class manages Reddit interactions, including scanning subreddits, posting comments, and logging actions.

**Current TODOs:**
- Implement adaptive posting strategies
- Implement anti-detection measures
- Add support for multiple bot account coordination

**Completed Improvements:**
- ✅ Implemented comprehensive post relevance detection algorithm
- ✅ Added comment performance tracking with database persistence
- ✅ Added intelligent comment reply selection (top 3 eligible comments)
- ✅ Improved error handling with custom exceptions and logging
- ✅ Standardized method signatures and return types
- ✅ Integrated with ResponseGenerator for coordinated response generation

### 6. Response Generator (`src/response_generator.py`)

Central orchestration component that coordinates the response generation workflow.

**Features:**
- ✅ Implements 5-stage pipeline pattern: Context → Analysis → Strategy → Template → Generation
- ✅ Provides proper validation and error handling between stages
- ✅ Streamlines workflow from context collection to final response generation
- ✅ Integrates with thread analysis for intelligent comment targeting
- ✅ Supports both submission replies and comment-to-comment responses

**Current TODOs:**
- Add response caching for similar contexts
- Implement A/B testing framework for different strategies
- Add performance metrics collection

### 7. Main Application (`src/main.py`)

The entry point for the application with scheduler setup.

**Current TODOs:**
- Implement monitoring and alerting
- Add dashboard for real-time status

**Completed Improvements:**
- ✅ Implemented proper shutdown handling
- ✅ Added comprehensive command-line interface

### 8. Testing Framework

Includes comprehensive test files for all major components.

**Current TODOs:**
- Add performance benchmarks for response generation pipeline
- Create a CI/CD pipeline with GitHub Actions
- Add integration tests for end-to-end workflows
- Implement load testing for scheduled operations

**Completed Improvements:**
- ✅ Expanded test coverage across core modules
- ✅ Implemented integration tests for agent workflows
- ✅ Added proper mocking for Reddit API and OpenAI API
- ✅ Created utility scripts for testing enhanced prompts and thread analysis
- ✅ Added pytest configuration for consistent test execution

## Prioritized User Stories / Issues

### High Priority (P0)

1. **Post Relevance Detection** ✅
   - As a bot operator, I want the bot to intelligently select which posts to comment on, so that it maximizes engagement and avoids wasting resources on irrelevant posts.
   - Tasks:
     - ✅ Implement post filtering based on content analysis
     - ✅ Add scoring algorithm for post relevance
     - ✅ Create configurable relevance thresholds

2. **Comment Performance Tracking** ✅
   - As a bot operator, I want to track how well each comment performs, so I can optimize the bot's commenting strategy.
   - Tasks:
     - ✅ Implement periodic checking of comment karma
     - ✅ Add performance metrics to database
     - Create performance reports

3. **Content Safety Measures**
   - As a bot operator, I want to ensure the bot doesn't generate inappropriate content, to maintain compliance with Reddit's rules and avoid bans.
   - Tasks:
     - Implement content filtering
     - Add sensitive topic detection
     - Create safety override mechanisms

### Medium Priority (P1)

4. **Multi-Subreddit Support**
   - As a bot operator, I want to configure different commenting strategies for different subreddits, to optimize the bot's performance across various communities.
   - Tasks:
     - Implement subreddit-specific configurations
     - Add subreddit analysis tools
     - Create subreddit performance comparisons

5. **Advanced Prompt Engineering** ✅
   - As a bot operator, I want to fine-tune the prompts sent to the LLM, to generate more relevant and engaging comments.
   - Tasks:
     - ✅ Create template system for prompts with multiple template types
     - ✅ Implement dynamic prompt construction with context awareness
     - ✅ Add representative comment sampling for style matching
     - ✅ Implement variation engine for natural language diversity
     - ✅ Add comment length adaptation based on subreddit patterns
     - Add A/B testing for prompt effectiveness

6. **Alternative LLM Provider Support**
   - As a bot operator, I want to use different LLM providers, to optimize cost and performance.
   - Tasks:
     - Add support for Claude, Llama, etc.
     - Implement provider switching logic
     - Create cost optimization strategies

7. **Dashboard & Monitoring**
   - As a bot operator, I want a dashboard to monitor the bot's activities and performance, to quickly identify issues and opportunities.
   - Tasks:
     - Create web-based dashboard
     - Implement real-time monitoring
     - Add alerting for critical issues

### Lower Priority (P2)

8. **Comment Reply Handling** ✅
   - As a bot operator, I want the bot to respond to replies to its comments, to increase engagement and appear more human-like.
   - Tasks:
     - ✅ Implement intelligent reply detection and selection
     - ✅ Add context-aware response generation for comment replies
     - ✅ Create conversation threading logic with comment forest analysis
     - ✅ Add enhanced comment context analysis for better targeting
     - ✅ Implement top-3 comment selection with score-based ranking

9. **Database Migration & Backup**
   - As a bot operator, I want automated database backups and smooth schema migrations, to ensure data integrity and easy updates.
   - Tasks:
     - Implement backup automation
     - Create migration scripts
     - Add data integrity validation

10. **Advanced Analytics**
    - As a bot operator, I want detailed analytics on the bot's performance, to gain insights and optimize strategies.
    - Tasks:
      - Create comprehensive reporting
      - Implement trend analysis
      - Add predictive modeling

11. **Anti-Detection Measures**
    - As a bot operator, I want the bot to avoid detection as an automated system, to ensure longevity on the platform.
    - Tasks:
      - Implement random timing variations
      - Add human-like behavior patterns
      - Create detection evasion strategies

12. **Multi-Bot Orchestration**
    - As a bot operator, I want to manage multiple bot accounts with different personalities, to diversify risk and increase total karma generation.
    - Tasks:
      - Implement bot identity management
      - Add coordination between bots
      - Create conflict avoidance strategies

## Implementation Roadmap

1. **Phase 1: Core Functionality Enhancements** ✅
   - ✅ Implement Post Relevance Detection with quality scoring (P0)
   - ✅ Add Comment Performance Tracking with database persistence (P0)
   - ✅ Add ResponseGenerator orchestration layer
   - Implement Content Safety Measures (P0)

2. **Phase 2: Platform Extensions** 🔄
   - Add Multi-Subreddit Support with subreddit-specific configurations (P1)
   - ✅ Implement Advanced Prompt Engineering with representative comments (P1)
   - ✅ Add dynamic comment length adaptation
   - Add Alternative LLM Provider Support (P1)

3. **Phase 3: Operational Improvements** 🔄
   - Create Dashboard & Monitoring (P1)
   - ✅ Implement intelligent Comment Reply Handling with context analysis (P2)
   - ✅ Add comprehensive CLI utilities for debugging and analysis
   - Add Database Migration & Backup (P2)

4. **Phase 4: Advanced Features**
   - Implement Advanced Analytics (P2)
   - Add Anti-Detection Measures (P2)
   - Create Multi-Bot Orchestration (P2)

5. **Phase 5: Code Structure Improvements** ✅
   - ✅ Modular utility functions with clear separation of concerns
   - ✅ Enhanced error handling and logging with component-specific loggers
   - ✅ Improved database operations with connection pooling
   - ✅ Standardized interfaces and method signatures
   - ✅ ResponseGenerator pipeline pattern for coordinated workflows
   - ✅ Comprehensive CLI interface with analysis utilities

## Technical Debt and Refactoring

- ✅ Improve error handling throughout the codebase
- ✅ Enhance logging for better debugging
- ✅ Refactor code for better modularity
- Optimize database queries for performance
- ✅ Implement comprehensive documentation

## New Technical Debt Items

### High Priority
- Refactor the main.py file to use the ResponseGenerator class consistently across all workflows
- Add comprehensive type hints to all functions for better IDE support and code maintainability
- Create a unified configuration system that combines environment variables and praw.ini
- Implement content filtering and safety measures for generated responses
- Add response caching system for similar contexts to optimize API usage

### Medium Priority
- Implement proper unit tests for all utility modules (database_utils, reddit_utils, etc.)
- Add integration tests for complete end-to-end workflows
- Create performance benchmarks for the response generation pipeline
- Implement A/B testing framework for different prompt strategies
- Add database migration system for schema updates

### Lower Priority
- Implement a proper CI/CD pipeline with GitHub Actions
- Add support for multiple LLM providers (Claude, Llama, etc.)
- Create web-based dashboard for monitoring bot performance
- Implement multi-bot orchestration for coordinated account management
- Add advanced analytics and predictive modeling for engagement optimization
