#!/usr/bin/env python3
"""
Database module for Project Authentica.
Handles all database interactions using SQLite3.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional, Any


# Database file path constant
DB_FILE = "data/authentica.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: A connection object to the database with foreign key support enabled.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """
    Initialize the database by creating necessary tables if they don't exist.
    
    Creates three tables:
    - bots: Stores information about Reddit bots
    - actions_log: Logs all actions performed by the bots
    - comment_performance: Tracks performance metrics of comments
    """
    # Create data directory if it doesn't exist
    data_dir = os.path.dirname(DB_FILE)
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create bots table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bots (
        bot_id INTEGER PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        last_used TEXT
    )
    ''')
    
    # Create actions_log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS actions_log (
        log_id INTEGER PRIMARY KEY,
        bot_username TEXT NOT NULL,
        action_type TEXT NOT NULL,
        target_id TEXT,
        status TEXT NOT NULL,
        details TEXT,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (bot_username) REFERENCES bots(username)
    )
    ''')
    
    # Create comment_performance table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comment_performance (
        perf_id INTEGER PRIMARY KEY,
        comment_id TEXT NOT NULL UNIQUE,
        submission_id TEXT NOT NULL,
        subreddit TEXT NOT NULL,
        initial_score INTEGER NOT NULL,
        current_score INTEGER NOT NULL,
        last_checked TEXT NOT NULL
    )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Initialize the database when script is run directly
    initialize_database()
    print(f"Database initialized successfully at {os.path.abspath(DB_FILE)}") 