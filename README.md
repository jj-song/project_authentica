# Project Authentica: AI-Assisted MVP Build Plan

This document serves as the official `README.md` and step-by-step construction guide for the Project Authentica MVP. It is the primary context-setting document for the AI assistant. Use this file to track the project's progress from start to finish.

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

## ✅ Project Tracker Checklist

Use this checklist to track your progress as you complete each step.

### **Phase 1: Setup & Environment**
- [ ] **Task 1:** Create project directory `project_authentica`.
- [ ] **Task 2:** Generate `requirements.txt` (including `pytest`) and `.gitignore`.
- [ ] **Task 3:** Install dependencies: `pip install -r requirements.txt`.
- [ ] **Task 4:** Create the `praw.ini` configuration file.

### **Phase 2: Core Module Generation**
- [ ] **Task 5:** Generate `src/database.py`.
- [ ] **Task 6:** Generate `src/config.py`.
- [ ] **Task 7:** Generate `src/utils.py`.
- [ ] **Task 8:** Generate `src/llm_handler.py`.
- [ ] **Task 9:** Generate `src/agent.py` with the `KarmaAgent` class.
- [ ] **Task 10:** Generate `src/main.py` to initialize and schedule the agent.

### **Phase 3: Unit Testing**
- [ ] **Task 11:** Create the `tests/` directory structure.
- [ ] **Task 12:** Write unit tests for `src/utils.py` in `tests/test_utils.py`.
- [ ] **Task 13:** Write unit tests for `src/database.py` logic in `tests/test_database.py`.
- [ ] **Task 14:** Write unit tests for `src/agent.py` in `tests/test_agent.py`, using mocks for PRAW and the database.

### **Phase 4: Integration & Deployment**
- [ ] **Task 15:** Run all tests and ensure they pass: `pytest`.
- [ ] **Task 16:** Initialize the database: `python src/database.py`.
- [ ] **Task 17:** Manually add the first bot's data to the `bots` table.
- [ ] **Task 18:** Run the application in a controlled test environment.
- [ ] **Task 19:** Monitor `data/authentica.db` and console output.
- [ ] **Task 20:** Deploy for the 30-day viability test.

---

## 🚀 Construction Plan: Task Overview

This section outlines the goals for each step of the construction process.

### **Task 1: Initial Project Setup**
**Goal:** Create the foundational files for dependencies (`requirements.txt`) and version control (`.gitignore`).

### **Task 2: Core Module Generation**
**Goal:** Generate all the source code modules (`database.py`, `config.py`, `utils.py`, `llm_handler.py`, `agent.py`, `main.py`) according to the project blueprint.

### **Task 3: Unit Testing**
**Goal:** Create a corresponding test file for each core module, ensuring that all business logic is covered by unit tests that follow the "Standing Orders."

### **Task 4: Final Configuration**
**Goal:** Create the `praw.ini` configuration file in the project's root directory with the bot's API credentials.

### **Task 5: Execution & Deployment**
**Goal:** Run the test suite, initialize the database, and start the application for its operational trial.
**Manual Follow-up:**
1.  Run the test suite: `pytest`
2.  Initialize the database: `python src/database.py`
3.  Start the bot: `python src/main.py`

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

### 3. Run the Bot

```bash
python src/main.py
```

## Project Structure

- `src/main.py`: Main entry point for the application
- `src/agent.py`: Contains the KarmaAgent class for Reddit interactions
- `src/config.py`: Handles Reddit API authentication
- `src/database.py`: Manages database connections and schema
- `src/llm_handler.py`: Handles interactions with language models
- `src/utils.py`: Utility functions for the project

## Database Schema

The project uses SQLite with the following tables:

- `bots`: Stores information about Reddit bots
- `actions_log`: Logs all actions performed by the bots
- `comment_performance`: Tracks performance metrics of comments

## Security Notes

- The `praw.ini` file contains sensitive information and is excluded from version control
- All data is stored locally in the `data/` directory, which is also excluded from version control