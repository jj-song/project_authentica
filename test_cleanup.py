#!/usr/bin/env python3
"""
Test script for the code structure cleanup.
"""

import os
import sys
import logging
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CleanupTest")

def test_imports():
    """Test that all modules can be imported correctly."""
    modules = [
        "src.utils.database_utils",
        "src.utils.reddit_utils",
        "src.utils.error_utils",
        "src.utils.logging_utils",
        "src.database",
        "src.agent",
        "src.context.collector",
        "src.context.templates",
        "src.thread_analysis.analyzer",
        "src.thread_analysis.strategies",
        "src.thread_analysis.conversation",
        "src.response_generator",
        "src.llm_handler",
        "src.config"
    ]
    
    success = True
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            logger.info(f"✅ Successfully imported {module_name}")
        except Exception as e:
            logger.error(f"❌ Failed to import {module_name}: {str(e)}")
            success = False
    
    return success

def test_database():
    """Test database initialization and connection."""
    try:
        from src.database import initialize_database, get_db_connection
        
        # Initialize database
        initialize_database()
        logger.info("✅ Database initialized successfully")
        
        # Test connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        logger.info(f"✅ Database connection successful. Found {len(tables)} tables")
        return True
    except Exception as e:
        logger.error(f"❌ Database test failed: {str(e)}")
        return False

def test_reddit_utils():
    """Test Reddit utilities (without actual authentication)."""
    try:
        from src.utils.reddit_utils import get_reddit_instance
        
        # Just test the import, don't actually authenticate
        logger.info("✅ Reddit utilities imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Reddit utilities test failed: {str(e)}")
        return False

def test_response_generator():
    """Test ResponseGenerator class (without actual Reddit instance)."""
    try:
        from src.response_generator import ResponseGenerator
        
        # Just test the import, don't actually create an instance
        logger.info("✅ ResponseGenerator imported successfully")
        return True
    except Exception as e:
        logger.error(f"❌ ResponseGenerator test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    logger.info("Starting code structure cleanup tests")
    
    tests = [
        ("Import Test", test_imports),
        ("Database Test", test_database),
        ("Reddit Utils Test", test_reddit_utils),
        ("Response Generator Test", test_response_generator)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        logger.info(f"\nRunning {test_name}...")
        if test_func():
            logger.info(f"{test_name} passed!")
        else:
            logger.error(f"{test_name} failed!")
            all_passed = False
    
    if all_passed:
        logger.info("\n✅ All tests passed! Code structure cleanup was successful.")
        return 0
    else:
        logger.error("\n❌ Some tests failed. Please check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 