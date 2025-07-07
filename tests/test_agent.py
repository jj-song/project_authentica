#!/usr/bin/env python3
"""
Unit tests for the KarmaAgent class in src/agent.py
"""

import pytest
import sqlite3
from unittest.mock import MagicMock, call, patch

import praw
from praw.exceptions import APIException, PRAWException

from src.agent import KarmaAgent


@pytest.fixture
def agent_setup(mocker):
    """
    Setup fixture that provides a mocked KarmaAgent instance for testing.
    
    This fixture creates mock objects for the Reddit instance and database connection,
    then instantiates a KarmaAgent with these mocks.
    
    Args:
        mocker: pytest-mock fixture
        
    Returns:
        tuple: (agent, mock_reddit, mock_db_conn) - The KarmaAgent instance and its mocked dependencies
    """
    # Create mock Reddit instance
    mock_reddit = mocker.MagicMock(spec=praw.Reddit)
    mock_reddit.user.me.return_value = "test_bot"
    
    # Create mock DB connection and cursor
    mock_db_conn = mocker.MagicMock(spec=sqlite3.Connection)
    mock_cursor = mocker.MagicMock(spec=sqlite3.Cursor)
    mock_db_conn.cursor.return_value = mock_cursor
    
    # Create the agent
    agent = KarmaAgent(mock_reddit, mock_db_conn)
    
    # Patch the logger to avoid actual logging during tests
    mocker.patch.object(agent, 'logger')
    
    return agent, mock_reddit, mock_db_conn


def test_scan_and_comment_success(agent_setup, mocker):
    """
    Test that scan_and_comment successfully posts a comment on a new submission.
    
    This test verifies that:
    1. The agent checks if it has already commented on the post
    2. It generates a comment using the LLM handler
    3. It posts the comment via the submission's reply method
    4. It logs the successful action to the database
    5. It creates a record in the comment_performance table
    """
    agent, mock_reddit, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Configure mock cursor to return empty result (no previous comment)
    mock_cursor.fetchone.return_value = None
    
    # Create mock submission
    mock_submission = mocker.MagicMock()
    mock_submission.id = "test_submission_id"
    mock_submission.title = "Test Submission"
    mock_submission.selftext = "This is a test submission."
    
    # Mock comment that will be returned by submission.reply()
    mock_comment = mocker.MagicMock()
    mock_comment.id = "test_comment_id"
    mock_submission.reply.return_value = mock_comment
    
    # Configure mock subreddit with our mock submission
    mock_subreddit = mocker.MagicMock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_reddit.subreddit.return_value = mock_subreddit
    
    # Mock the LLM handler's generate_comment function
    test_comment = "This is a helpful, AI-generated test comment."
    mocker.patch('src.llm_handler.generate_comment', return_value=test_comment)
    
    # Call the method under test
    agent.scan_and_comment("testsubreddit", 1)
    
    # Verify Reddit API interactions
    mock_reddit.subreddit.assert_called_once_with("testsubreddit")
    mock_subreddit.hot.assert_called_once_with(limit=1)
    mock_submission.reply.assert_called_once_with(test_comment)
    
    # Verify database interactions for logging the action
    assert mock_db_conn.cursor.call_count >= 2
    
    # Check that we logged a successful comment action
    execute_calls = mock_cursor.execute.call_args_list
    
    # Find the call that logs the successful comment
    comment_log_call = None
    for call_obj in execute_calls:
        args, _ = call_obj
        sql = args[0]
        if "INSERT INTO actions_log" in sql and len(args) > 1:
            params = args[1]
            if params[0] == "test_bot" and params[1] == "COMMENT" and params[3] == "SUCCESS":
                comment_log_call = call_obj
                break
    
    assert comment_log_call is not None, "No successful comment action was logged"
    
    # Check that we created a record in comment_performance
    performance_log_call = None
    for call_obj in execute_calls:
        args, _ = call_obj
        sql = args[0]
        if "INSERT INTO comment_performance" in sql:
            performance_log_call = call_obj
            break
    
    assert performance_log_call is not None, "No comment performance record was created"
    
    # Verify that we committed the database changes
    assert mock_db_conn.commit.call_count >= 1


def test_scan_and_comment_skips_processed_post(agent_setup, mocker):
    """
    Test that scan_and_comment skips posts that have already been commented on.
    
    This test verifies that:
    1. The agent checks the actions_log table for previous comments
    2. When a previous successful comment is found, it skips the post
    3. No new comment is posted
    4. No new database entries are made for that post
    """
    agent, mock_reddit, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Configure mock cursor to return a result (previous comment exists)
    mock_cursor.fetchone.return_value = (1,)
    
    # Create mock submission
    mock_submission = mocker.MagicMock()
    mock_submission.id = "already_commented_id"
    
    # Configure mock subreddit with our mock submission
    mock_subreddit = mocker.MagicMock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_reddit.subreddit.return_value = mock_subreddit
    
    # Call the method under test
    agent.scan_and_comment("testsubreddit", 1)
    
    # Verify Reddit API interactions
    mock_reddit.subreddit.assert_called_once_with("testsubreddit")
    mock_subreddit.hot.assert_called_once_with(limit=1)
    
    # Verify that reply was never called on the submission
    mock_submission.reply.assert_not_called()
    
    # Reset the mock to track new calls for database operations
    mock_cursor.execute.reset_mock()
    mock_db_conn.commit.reset_mock()
    
    # Verify no new comment actions were logged for this submission
    for call_obj in mock_cursor.execute.call_args_list:
        args, _ = call_obj
        if len(args) > 1 and isinstance(args[1], tuple) and len(args[1]) > 2:
            # Check if this is an insert into actions_log for this submission
            if args[1][1] == "COMMENT" and args[1][2] == "already_commented_id":
                assert False, "Should not log new actions for already processed posts"


def test_scan_and_comment_handles_api_failure(agent_setup, mocker):
    """
    Test that scan_and_comment handles PRAW API exceptions gracefully.
    
    This test verifies that:
    1. When posting a comment fails with an APIException
    2. The agent catches the exception
    3. It logs a FAILURE action to the database
    4. The failure details include the exception message
    """
    agent, mock_reddit, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Configure mock cursor to return empty result (no previous comment)
    mock_cursor.fetchone.return_value = None
    
    # Create mock submission that raises an exception when reply is called
    mock_submission = mocker.MagicMock()
    mock_submission.id = "error_submission_id"
    mock_submission.title = "Test Submission"
    mock_submission.selftext = "This is a test submission."
    
    # Configure the reply method to raise an APIException
    api_error_message = "API rate limit exceeded"
    mock_submission.reply.side_effect = APIException(api_error_message)
    
    # Configure mock subreddit with our mock submission
    mock_subreddit = mocker.MagicMock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_reddit.subreddit.return_value = mock_subreddit
    
    # Mock the LLM handler's generate_comment function
    test_comment = "This comment will fail to post."
    mocker.patch('src.llm_handler.generate_comment', return_value=test_comment)
    
    # Call the method under test
    agent.scan_and_comment("testsubreddit", 1)
    
    # Verify Reddit API interactions
    mock_reddit.subreddit.assert_called_once_with("testsubreddit")
    mock_subreddit.hot.assert_called_once_with(limit=1)
    mock_submission.reply.assert_called_once_with(test_comment)
    
    # Verify database interactions for logging the failure
    # Find the call that logs the failed comment
    failure_log_call = None
    for call_obj in mock_cursor.execute.call_args_list:
        args, _ = call_obj
        if "INSERT INTO actions_log" in args[0] and len(args) > 1:
            params = args[1]
            if (params[0] == "test_bot" and 
                params[1] == "COMMENT" and 
                params[2] == "error_submission_id" and 
                params[3] == "FAILURE" and 
                api_error_message in str(params[4])):
                failure_log_call = call_obj
                break
    
    assert failure_log_call is not None, "No failure action was logged for the API exception"
    
    # Verify that we committed the database changes
    assert mock_db_conn.commit.call_count >= 1


def test_scan_and_comment_handles_general_exception(agent_setup, mocker):
    """
    Test that scan_and_comment handles unexpected exceptions gracefully.
    
    This test verifies that:
    1. When an unexpected exception occurs during comment posting
    2. The agent catches the exception
    3. It logs a FAILURE action to the database
    4. The failure details include the exception message
    """
    agent, mock_reddit, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Configure mock cursor to return empty result (no previous comment)
    mock_cursor.fetchone.return_value = None
    
    # Create mock submission that raises an exception when reply is called
    mock_submission = mocker.MagicMock()
    mock_submission.id = "error_submission_id"
    mock_submission.title = "Test Submission"
    mock_submission.selftext = "This is a test submission."
    
    # Configure the reply method to raise a generic Exception
    error_message = "Unexpected error"
    mock_submission.reply.side_effect = Exception(error_message)
    
    # Configure mock subreddit with our mock submission
    mock_subreddit = mocker.MagicMock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_reddit.subreddit.return_value = mock_subreddit
    
    # Mock the LLM handler's generate_comment function
    test_comment = "This comment will fail to post."
    mocker.patch('src.llm_handler.generate_comment', return_value=test_comment)
    
    # Call the method under test
    agent.scan_and_comment("testsubreddit", 1)
    
    # Verify Reddit API interactions
    mock_reddit.subreddit.assert_called_once_with("testsubreddit")
    mock_subreddit.hot.assert_called_once_with(limit=1)
    mock_submission.reply.assert_called_once_with(test_comment)
    
    # Verify database interactions for logging the failure
    # Find the call that logs the failed comment
    failure_log_call = None
    for call_obj in mock_cursor.execute.call_args_list:
        args, _ = call_obj
        if "INSERT INTO actions_log" in args[0] and len(args) > 1:
            params = args[1]
            if (params[0] == "test_bot" and 
                params[1] == "COMMENT" and 
                params[2] == "error_submission_id" and 
                params[3] == "FAILURE" and 
                error_message in str(params[4])):
                failure_log_call = call_obj
                break
    
    assert failure_log_call is not None, "No failure action was logged for the unexpected exception"


def test_is_post_relevant(agent_setup):
    """
    Test that _is_post_relevant returns True for the MVP implementation.
    
    In the MVP, this method always returns True. This test ensures that
    behavior is maintained until more sophisticated relevance checking is implemented.
    """
    agent, _, _ = agent_setup
    mock_submission = MagicMock()
    
    result = agent._is_post_relevant(mock_submission)
    
    assert result is True, "In MVP, _is_post_relevant should always return True"


def test_log_action(agent_setup, mocker):
    """
    Test that _log_action correctly logs actions to the database.
    
    This test verifies that:
    1. The _log_action method formats the parameters correctly
    2. It executes an INSERT statement on the actions_log table
    3. It commits the changes to the database
    """
    agent, _, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Call the method under test
    action_type = "TEST_ACTION"
    target_id = "test_target"
    status = "TEST_STATUS"
    details = "Test details"
    
    agent._log_action(action_type, target_id, status, details)
    
    # Verify database interactions
    mock_db_conn.cursor.assert_called_once()
    
    # Check that execute was called with the correct SQL and parameters
    execute_call = mock_cursor.execute.call_args
    args, _ = execute_call
    
    # Verify the SQL contains an INSERT INTO actions_log
    assert "INSERT INTO actions_log" in args[0]
    
    # Verify the parameters match what we provided
    params = args[1]
    assert params[0] == "test_bot"  # bot_username
    assert params[1] == action_type
    assert params[2] == target_id
    assert params[3] == status
    assert params[4] == details
    
    # Verify that we committed the changes
    mock_db_conn.commit.assert_called_once() 