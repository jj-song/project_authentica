# Project Authentica Scripts

This directory contains utility scripts for testing and running specific components of Project Authentica. Most functionality has been consolidated into the main CLI interface in `src/main.py` to reduce redundancy and provide a more consistent user experience.

## Available Scripts

### `test_thread_analysis.py`
Tests the thread analysis functionality in isolation. This is useful for debugging and developing the thread analysis component.

```bash
python scripts/test_thread_analysis.py SUBMISSION_ID
```

Example output:
```
Thread Analysis Results:
- Total Comments: 42
- Max Depth: 8
- Top Contributors: ['user1', 'user2', 'user3']
- Key Topics: ['performance', 'updates', 'issues']
- Conversation Hotspots: 3 identified
```

### `test_enhanced_prompts.py`
Tests the enhanced prompt engineering with dynamic templates and variations. This is useful for developing and debugging the prompt engineering system.

```bash
python scripts/test_enhanced_prompts.py
```

Example output:
```
Selected Template: PersonaBasedTemplate
Applied Variations: 
- "Use more casual language and contractions"
- "Include a personal anecdote or example"
Generated Prompt:
[Prompt content will appear here]
```

## Removed Scripts

The following scripts have been removed as part of the code cleanup, with their functionality now integrated into the main CLI interface:

- `test_bot_run.py`: Replaced by `python -m src.main --once`
- `test_run.py`: Replaced by `python -m src.main --once --dry-run`
- `test_openai.py`: Functionality integrated into `test_enhanced_prompts.py`
- `test_config.py`: Configuration testing now handled by unit tests
- `view_comment.py`: Replaced by `python -m src.main --check-comment COMMENT_ID`
- `show_context.py`: Replaced by `python -m src.main --show-context SUBMISSION_ID`

## Using the CLI Interface

Most functionality is now accessible through the comprehensive CLI in `src/main.py`:

```bash
# Run the bot once without scheduling
python -m src.main --once --subreddit AskReddit --limit 1

# View comments on a specific post
python -m src.main --view-comments SUBMISSION_ID

# Show context collected for a specific submission
python -m src.main --show-context SUBMISSION_ID

# Check status and performance of a specific comment
python -m src.main --check-comment COMMENT_ID --verbose

# Run in dry-run mode (no actual comments posted)
python -m src.main --once --dry-run --verbose
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Ensure your praw.ini file has the correct credentials
   - Check if your Reddit account is shadowbanned using `python -m src.main --check-shadowban USERNAME`

2. **API Rate Limits**
   - If you encounter rate limit errors, increase the interval between runs
   - Use `--jitter` to add randomness to the timing

3. **Database Errors**
   - If you encounter database errors, try running `python -m src.main --repair-db` to fix common issues

## Further Documentation

For a complete overview of all available CLI options, please see the README.md or run:

```bash
python -m src.main --help
```
