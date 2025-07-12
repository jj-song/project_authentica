# Project Authentica Scripts

This directory previously contained utility scripts for testing and running the Project Authentica bot. These scripts have now been consolidated into the main CLI interface in `src/main.py` to reduce redundancy and provide a more consistent user experience.

## Using the CLI Interface

All functionality that was previously available through separate scripts is now accessible through the comprehensive CLI:

```bash
# Run the bot once without scheduling
python -m src.main --once --subreddit AskReddit --limit 1

# View comments on a specific post
python -m src.main --view-comments SUBMISSION_ID

# Show context collected for a specific submission
python -m src.main --show-context SUBMISSION_ID

# Check status and performance of a specific comment
python -m src.main --check-comment COMMENT_ID --verbose
```

## Remaining Test Scripts

### `test_bot_run.py` and `test_run.py`
Test scripts for running the bot without the scheduler. This functionality is now available with:
```bash
python -m src.main --once
```

### `test_openai.py`
Tests the OpenAI integration. Similar functionality can be achieved with:
```bash
python -m src.main --once --dry-run --verbose
```

### `test_thread_analysis.py`
Tests the thread analysis functionality. Similar information can be viewed with:
```bash
python -m src.main --show-context SUBMISSION_ID --verbose
```

## Further Documentation

For a complete overview of all available CLI options, please see the README.md or run:

```bash
python -m src.main --help
```
