# Testing Plan for Project Authentica

This document identifies the functions that need unit tests across the project.

## Core Modules

### 1. src/agent.py
- `KarmaAgent.__init__`: Test initialization with mock Reddit and DB
- `KarmaAgent.scan_and_comment`: Test the main workflow with mocked submissions
- `KarmaAgent._process_submission`: Test submission processing logic
- `KarmaAgent._try_reply_to_comment`: Test comment reply logic
- `KarmaAgent._is_post_relevant`: Test relevance determination
- `KarmaAgent._log_action`: Test logging to database

### 2. src/llm_handler.py
- `create_prompt`: Test prompt creation with different inputs and thread analysis
- `_create_basic_prompt`: Test fallback prompt creation
- `call_openai_api`: Test API call with mocked responses
- `clean_response`: Test response cleaning
- `generate_comment_from_submission`: Test end-to-end comment generation
- `generate_comment`: Test legacy comment generation

### 3. src/database.py
- `get_db_connection`: Test connection creation
- `initialize_database`: Test database initialization and table creation

### 4. src/config.py
- `get_reddit_instance`: Test Reddit instance creation with mock configs

### 5. src/utils.py
- `check_shadowban`: Test shadowban checking with mocked responses

## Context Module

### 1. src/context/collector.py
- `ContextCollector.__init__`: Test initialization
- `ContextCollector.collect_context`: Test context collection
- `ContextCollector._get_submission_context`: Test submission context extraction
- `ContextCollector._get_subreddit_context`: Test subreddit context extraction
- `ContextCollector._get_comments_context`: Test comments context extraction
- `ContextCollector._get_temporal_context`: Test temporal context extraction

### 2. src/context/templates.py
- `TemplateSelector.select_template`: Test template selection logic
- `TemplateSelector.generate_with_variations`: Test prompt generation with variations
- `VariationEngine.apply_variations`: Test variation application
- `StandardPromptTemplate.generate`: Test standard template generation
- `SubredditSpecificTemplate.generate`: Test subreddit-specific template generation
- `PersonaBasedTemplate.generate`: Test persona-based template generation
- `ContentTypeTemplate.generate`: Test content type-based template generation
- `CommentReplyTemplate.generate`: Test comment reply template generation

## Thread Analysis Module

### 1. src/thread_analysis/analyzer.py
- `ThreadAnalyzer.__init__`: Test initialization
- `ThreadAnalyzer.analyze_thread`: Test thread analysis
- `ThreadAnalyzer._extract_comment_forest`: Test comment forest extraction
- `ThreadAnalyzer._process_comment`: Test comment processing
- `ThreadAnalyzer._count_comments`: Test comment counting
- `ThreadAnalyzer._calculate_max_depth`: Test depth calculation
- `ThreadAnalyzer._extract_key_topics`: Test topic extraction
- `ThreadAnalyzer._analyze_sentiment`: Test sentiment analysis
- `ThreadAnalyzer._analyze_user_engagement`: Test user engagement analysis
- `ThreadAnalyzer._identify_top_contributors`: Test top contributor identification

### 2. src/thread_analysis/conversation.py
- `ConversationFlow.analyze`: Test conversation flow analysis
- `ConversationFlow._build_conversation_graph`: Test graph building
- `ConversationFlow._calculate_branching_factor`: Test branching factor calculation
- `ConversationFlow._identify_chains`: Test chain identification
- `ConversationFlow._calculate_conversation_density`: Test density calculation
- `ConversationFlow._identify_reply_patterns`: Test pattern identification
- `ConversationFlow._identify_hotspots`: Test hotspot identification

### 3. src/thread_analysis/strategies.py
- `ResponseStrategy.determine_strategy`: Test strategy determination
- `ResponseStrategy._adjust_weights`: Test weight adjustment
- `ResponseStrategy._select_weighted_strategy`: Test strategy selection
- `ResponseStrategy._determine_target_comment`: Test target comment determination
- `ResponseStrategy._generate_prompt_enhancements`: Test enhancement generation
- `ResponseStrategy._extract_question`: Test question extraction
- `ResponseStrategy._generate_strategy_reasoning`: Test reasoning generation

## Priority Order for Implementation

1. Core utility functions (utils.py, config.py, database.py)
2. LLM handler functions (llm_handler.py)
3. Context collection functions (context/collector.py)
4. Template generation functions (context/templates.py)
5. Agent functions (agent.py)
6. Thread analysis functions (thread_analysis/analyzer.py)
7. Conversation flow analysis functions (thread_analysis/conversation.py)
8. Response strategy functions (thread_analysis/strategies.py)

## Testing Approach

For each function:
1. Test normal operation with valid inputs
2. Test edge cases and boundary conditions
3. Test error handling and exceptions
4. Use mocks for external dependencies (Reddit API, OpenAI API, database)
5. Use fixtures for common test data

## Dependencies to Mock

- `praw.Reddit`: Mock Reddit instance and its methods
- `sqlite3.Connection`: Mock database connection and cursor
- `openai.OpenAI`: Mock OpenAI client and API responses
- `requests.get`: Mock HTTP responses for shadowban checking
- `datetime.datetime`: Mock current time for temporal context 