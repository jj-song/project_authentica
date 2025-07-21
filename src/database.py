#!/usr/bin/env python3
"""
Database module for Project Authentica.
Handles all database interactions using SQLite3.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime

from src.utils.error_utils import DatabaseError, handle_exceptions
from src.utils.logging_utils import get_component_logger

# Configure logging
logger = get_component_logger("database")

# Database file path constant
DB_FILE = "data/authentica.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: A connection object to the database with foreign key support enabled.
    """
    try:
        # Create data directory if it doesn't exist
        data_dir = os.path.dirname(DB_FILE)
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Failed to create database connection: {str(e)}")
        raise DatabaseError(f"Database connection error: {str(e)}")


@handle_exceptions
def initialize_database() -> None:
    """
    Initialize the database by creating necessary tables if they don't exist.
    
    Creates three tables:
    - bots: Stores information about Reddit bots
    - actions_log: Logs all actions performed by the bots
    - comment_performance: Tracks performance metrics of comments
    """
    logger.info("Initializing database...")
    
    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
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
        
        # Create table for comment samples if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comment_samples (
            id TEXT PRIMARY KEY,
            subreddit TEXT NOT NULL,
            author TEXT NOT NULL,
            body TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_utc REAL NOT NULL,
            submission_id TEXT NOT NULL,
            is_top_level INTEGER NOT NULL,
            collected_at REAL NOT NULL
        )
        ''')
        
        # Create table for subreddit profiles if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subreddit_profiles (
            subreddit TEXT PRIMARY KEY,
            profile TEXT NOT NULL,
            updated_at REAL NOT NULL
        )
        ''')
        
        # Create table for subreddit personalities if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subreddit_personalities (
            subreddit TEXT PRIMARY KEY,
            tone TEXT NOT NULL,
            formality_level REAL NOT NULL,
            judgment_style TEXT NOT NULL,
            empathy_level REAL NOT NULL,
            directness_level REAL NOT NULL,
            humor_usage REAL NOT NULL,
            advice_approach TEXT NOT NULL,
            questioning_pattern TEXT NOT NULL,
            agreement_tendency REAL NOT NULL,
            length_preference TEXT NOT NULL,
            structure_preference TEXT NOT NULL,
            raw_analysis TEXT NOT NULL,
            updated_at REAL NOT NULL,
            sample_count INTEGER NOT NULL
        )
        ''')
        
        # Commit changes
        conn.commit()
        logger.info("Database tables created successfully")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating database tables: {str(e)}")
        raise DatabaseError(f"Database initialization error: {str(e)}")
    finally:
        conn.close()


def ensure_bot_registered(db_conn: sqlite3.Connection, username: str) -> None:
    """
    Ensure a bot is registered in the bots table to prevent foreign key constraint failures.
    
    Args:
        db_conn (sqlite3.Connection): Database connection
        username (str): Bot username to register
    """
    try:
        cursor = db_conn.cursor()
        # Check if bot already exists
        cursor.execute("SELECT * FROM bots WHERE username = ?", (username,))
        if not cursor.fetchone():
            # Bot doesn't exist, register it
            current_time = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO bots (username, status, created_at) VALUES (?, ?, ?)",
                (username, "active", current_time)
            )
            db_conn.commit()
            logger.info(f"Registered bot '{username}' in database")
    except sqlite3.Error as e:
        logger.error(f"Database error when registering bot: {str(e)}")
        # Don't raise the exception, as this is a preventative measure


class DatabaseManager:
    """
    Manages database operations with connection pooling and standardized methods.
    """
    
    def __init__(self):
        """Initialize the DatabaseManager."""
        self.connection = None
    
    def __enter__(self):
        """Context manager entry point."""
        self.connection = get_db_connection()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point."""
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a database query and return results as a list of dictionaries.
        
        Args:
            query (str): SQL query to execute
            params (tuple): Parameters for the query
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            # If this is a SELECT query, return the results
            if query.strip().upper().startswith("SELECT"):
                return [dict(row) for row in cursor.fetchall()]
            
            # For other queries, commit and return empty list
            self.connection.commit()
            return []
        except sqlite3.Error as e:
            self.connection.rollback()
            logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Query execution error: {str(e)}")
    
    def log_action(self, bot_username: str, action_type: str, target_id: str, 
                  status: str, details: Optional[str] = None) -> None:
        """
        Log an action to the actions_log table.
        
        Args:
            bot_username (str): Username of the bot
            action_type (str): Type of action
            target_id (str): ID of the target
            status (str): Status of the action
            details (Optional[str]): Additional details
        """
        # Ensure bot is registered to prevent foreign key constraint failures
        ensure_bot_registered(self.connection, bot_username)
        
        timestamp = datetime.now().isoformat()
        self.execute_query(
            """
            INSERT INTO actions_log 
            (bot_username, action_type, target_id, status, details, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (bot_username, action_type, target_id, status, details, timestamp)
        )
        
        # Update last_used timestamp for the bot
        self.execute_query(
            "UPDATE bots SET last_used = ? WHERE username = ?",
            (timestamp, bot_username)
        )


if __name__ == "__main__":
    # Initialize the database when script is run directly
    initialize_database()
    print(f"Database initialized successfully at {os.path.abspath(DB_FILE)}") 