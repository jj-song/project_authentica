# Project Authentica: AI-Assisted Reddit Bot

This document serves as the official `README.md` for the Project Authentica. Project Authentica is a Reddit bot system that posts AI-generated comments using OpenAI's API.

---

## 🤖 Standing Orders for AI Assistant

**These rules must be followed for all code generation and modification tasks:**

1.  **Unit Testing is Mandatory:** For every new function or class method containing business logic, generate a corresponding unit test.
    * **Framework:** Use the `pytest` framework for all tests. You will need to add it to `requirements.txt`.
    * **Location:** All test files must be placed in a parallel `tests/` directory at the project root. The structure inside `tests/` must mirror the `src/` directory (e.g., tests for `src/agent.py` go into `tests/test_agent.py`).
    * **Mocking:** Use `pytest-mock` or `unittest.mock` to isolate functions and classes from external dependencies like network requests (PRAW API calls) and database connections during testing.

2.  **Code Quality & Style:**
    * **Docstrings & Type Hinting:** All functions, classes, and methods must include comprehensive Google-style docstrings and full Python type hinting.
    * **Modularity:** Keep functions and classes focused on a single responsibility. If a component becomes overly complex, refactor it into smaller, more manageable units.

3.  **Security First:**
    * **No Hardcoded Secrets:** Never write sensitive information like API keys, secrets, or passwords directly in the source code. Always retrieve them from configuration files (`praw.ini`) or environment variables.

4.  **Robust Error Handling:**
    * Implement specific and robust `try...except` blocks for all operations that can fail, especially network I/O (API calls), file operations, and database interactions. Avoid generic `except Exception:`.

---

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Reddit API Credentials

Before running the bot, you need to set up your Reddit API credentials in the `praw.ini` file:

1. Create a Reddit App at https://www.reddit.com/prefs/apps
2. Select "script" as the application type
3. Set the redirect URI to http://localhost:8080
4. After creating the app, you'll receive a client ID and client secret
5. Edit the `praw.ini` file in the project root with your credentials:

```ini
[my_first_bot]
client_id=YOUR_CLIENT_ID_FROM_REDDIT
client_secret=YOUR_CLIENT_SECRET_FROM_REDDIT
user_agent=python:project_authentica:v1.0 (by /u/YOUR_REDDIT_USERNAME)
username=YOUR_BOTS_REDDIT_USERNAME
password=YOUR_BOTS_REDDIT_PASSWORD
```

### 3. Configure OpenAI API

1. Copy `env.example` to `.env`
2. Add your OpenAI API key to the `.env` file:

```
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=250
```

### 4. Initialize the Database

```bash
python src/database.py
```

### 5. Run the Bot

```bash
python src/main.py
```

## Project Structure

- `src/`: Source code for the application
  - `main.py`: Main entry point for the application
  - `agent.py`: Contains the KarmaAgent class for Reddit interactions
  - `config.py`: Handles Reddit API authentication
  - `database.py`: Manages database connections and schema
  - `llm_handler.py`: Handles interactions with language models
  - `utils.py`: Utility functions for the project

- `tests/`: Unit tests for the application
  - `test_agent.py`: Tests for the KarmaAgent class
  - `test_utils.py`: Tests for utility functions
  - `test_llm_handler.py`: Tests for the LLM handler

- `scripts/`: Utility scripts for testing and running the bot
  - `test_bot_run.py`: Test the bot on r/testingground4bots
  - `test_run.py`: Run the bot without the scheduler
  - `test_openai.py`: Test the OpenAI integration
  - `check_comment.py`: Check comments made by the bot

- `docs/`: Documentation files
  - `scope.md`: Comprehensive project scope and roadmap

- `data/`: Database and data files (not tracked in git)

## Database Schema

The project uses SQLite with the following tables:

- `bots`: Stores information about Reddit bots
- `actions_log`: Logs all actions performed by the bots
- `comment_performance`: Tracks performance metrics of comments

## Security Notes

- The `praw.ini` file contains sensitive information and is excluded from version control
- The `.env` file contains OpenAI API keys and is excluded from version control
- All data is stored locally in the `data/` directory, which is also excluded from version control

## Development Roadmap

For a detailed roadmap of planned features and improvements, see [docs/scope.md](docs/scope.md).
