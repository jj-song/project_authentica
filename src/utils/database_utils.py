#!/usr/bin/env python3
"""
Database utility functions for Project Authentica.
Provides centralized database operations and connection management.
"""

import sqlite3
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import os

# Configure logging
logger = logging.getLogger(__name__)

# Database file path constant
DB_FILE = "data/authentica.db"

def get_db_connection() -> sqlite3.Connection:
    """
    Create and return a connection to the SQLite database.
    Ensures the data directory exists.
    
    Returns:
        sqlite3.Connection: A connection object to the database with foreign key support enabled.
    """
    # Create data directory if it doesn't exist
    data_dir = os.path.dirname(DB_FILE)
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

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
            import datetime
            current_time = datetime.datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO bots (username, status, created_at) VALUES (?, ?, ?)",
                (username, "active", current_time)
            )
            db_conn.commit()
            logger.info(f"Registered bot '{username}' in database")
    except sqlite3.Error as e:
        logger.error(f"Database error when registering bot: {str(e)}")
        # Don't raise the exception, as this is a preventative measure

def execute_query(db_conn: sqlite3.Connection, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Execute a database query and return results as a list of dictionaries.
    
    Args:
        db_conn (sqlite3.Connection): Database connection
        query (str): SQL query to execute
        params (tuple): Parameters for the query
        
    Returns:
        List[Dict[str, Any]]: Query results
    """
    try:
        cursor = db_conn.cursor()
        cursor.execute(query, params)
        
        # If this is a SELECT query, return the results
        if query.strip().upper().startswith("SELECT"):
            return [dict(row) for row in cursor.fetchall()]
        
        # For other queries, commit and return empty list
        db_conn.commit()
        return []
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise

def close_connection(db_conn: Optional[sqlite3.Connection]) -> None:
    """
    Safely close a database connection.
    
    Args:
        db_conn (Optional[sqlite3.Connection]): Database connection to close
    """
    if db_conn:
        try:
            db_conn.close()
            logger.debug("Database connection closed")
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {str(e)}") 