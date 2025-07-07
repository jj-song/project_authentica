# Project Authentica Scripts

This directory contains utility scripts for testing and running the Project Authentica bot.

## Scripts Overview

### `test_bot_run.py`
A script to test the bot with OpenAI integration on the testingground4bots subreddit. It:
- Authenticates with Reddit
- Initializes the database connection
- Creates a KarmaAgent
- Scans for posts and comments on them
- Uses the 'new' sort to find recent posts

### `test_run.py`
A simple test script to run the bot without the scheduler. It:
- Sets up the environment
- Initializes the database
- Creates a KarmaAgent
- Performs a single scan

### `test_openai.py`
A script to test the OpenAI integration. It:
- Tests the comment generation using OpenAI's API
- Displays the generated comment
- Does not post to Reddit

### `check_comment.py`
A utility script to check comments made by the bot on a specific post. It:
- Fetches a post by ID
- Displays the post title and body
- Lists all comments on the post with their authors

## Usage

To run any script, use:

```bash
python scripts/<script_name>.py
```

For example:
```bash
python scripts/test_bot_run.py
```
