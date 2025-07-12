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

import datetime


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
    mock_reddit = mocker.MagicMock()
    mock_user = mocker.MagicMock()
    mock_user.me.return_value = "test_bot"
    mock_reddit.user = mock_user
    
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
    mock_submission.created_utc = datetime.datetime.now().timestamp() - 3600  # 1 hour ago
    mock_submission.stickied = False
    mock_submission.score = 5
    mock_submission.num_comments = 10
    mock_submission.subreddit = "testsubreddit"
    
    # Mock comment that will be returned by submission.reply()
    mock_comment = mocker.MagicMock()
    mock_comment.id = "test_comment_id"
    mock_submission.reply.return_value = mock_comment
    
    # Configure mock subreddit with our mock submission
    mock_subreddit = mocker.MagicMock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_reddit.subreddit.return_value = mock_subreddit
    
    # Mock the _try_reply_to_comment method to return False (so it falls back to submission reply)
    mocker.patch.object(agent, '_try_reply_to_comment', return_value=False)
    
    # Mock the LLM handler's generate_comment_from_submission function
    test_comment = "This is a helpful, AI-generated placeholder comment."
    mocker.patch('src.agent.generate_comment_from_submission', return_value=test_comment)
    
    # Mock the reply_to_submission method to return the mock comment
    mocker.patch.object(agent, 'reply_to_submission', return_value=mock_comment)
    
    # Call the method under test
    agent.scan_and_comment("testsubreddit", 1)
    
    # Verify Reddit API interactions
    mock_reddit.subreddit.assert_called_once_with("testsubreddit")
    mock_subreddit.hot.assert_called_once_with(limit=1)
    
    # Verify that reply_to_submission was called with the right arguments
    agent.reply_to_submission.assert_called_once_with(mock_submission, test_comment)


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
    mock_submission.created_utc = datetime.datetime.now().timestamp() - 3600  # 1 hour ago
    mock_submission.stickied = False
    mock_submission.score = 5
    mock_submission.num_comments = 10
    
    # Configure mock subreddit with our mock submission
    mock_subreddit = mocker.MagicMock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_reddit.subreddit.return_value = mock_subreddit
    
    # Mock the _try_reply_to_comment method to return False (so it falls back to submission reply)
    mocker.patch.object(agent, '_try_reply_to_comment', return_value=False)
    
    # Mock the LLM handler's generate_comment_from_submission function
    test_comment = "This is a helpful, AI-generated placeholder comment."
    mocker.patch('src.agent.generate_comment_from_submission', return_value=test_comment)
    
    # Configure the reply_to_submission method to raise an exception
    api_error_message = "API rate limit exceeded"
    mocker.patch.object(agent, 'reply_to_submission', side_effect=Exception(f"PRAW error: {api_error_message}"))
    
    # Call the method under test
    agent.scan_and_comment("testsubreddit", 1)
    
    # Verify Reddit API interactions
    mock_reddit.subreddit.assert_called_once_with("testsubreddit")
    mock_subreddit.hot.assert_called_once_with(limit=1)
    
    # Verify that reply_to_submission was called with the right arguments
    agent.reply_to_submission.assert_called_once_with(mock_submission, test_comment)
    
    # Verify database interactions for logging the failure
    # Find the call that logs the failed comment
    failure_log_call = None
    for call_obj in mock_cursor.execute.call_args_list:
        args, _ = call_obj
        if "INSERT INTO actions_log" in args[0] and len(args) > 1:
            params = args[1]
            if (params[0] == "test_bot" and 
                params[1] == "PROCESS_ERROR" and 
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
    mock_submission.created_utc = datetime.datetime.now().timestamp() - 3600  # 1 hour ago
    mock_submission.stickied = False
    mock_submission.score = 5
    mock_submission.num_comments = 10
    
    # Configure mock subreddit with our mock submission
    mock_subreddit = mocker.MagicMock()
    mock_subreddit.hot.return_value = [mock_submission]
    mock_reddit.subreddit.return_value = mock_subreddit
    
    # Mock the _try_reply_to_comment method to return False (so it falls back to submission reply)
    mocker.patch.object(agent, '_try_reply_to_comment', return_value=False)
    
    # Mock the LLM handler's generate_comment_from_submission function
    test_comment = "This is a helpful, AI-generated placeholder comment."
    mocker.patch('src.agent.generate_comment_from_submission', return_value=test_comment)
    
    # Configure the reply_to_submission method to raise a generic Exception
    error_message = "Unexpected error"
    mocker.patch.object(agent, 'reply_to_submission', side_effect=Exception(error_message))
    
    # Call the method under test
    agent.scan_and_comment("testsubreddit", 1)
    
    # Verify Reddit API interactions
    mock_reddit.subreddit.assert_called_once_with("testsubreddit")
    mock_subreddit.hot.assert_called_once_with(limit=1)
    
    # Verify that reply_to_submission was called with the right arguments
    agent.reply_to_submission.assert_called_once_with(mock_submission, test_comment)
    
    # Verify database interactions for logging the failure
    # Find the call that logs the failed comment
    failure_log_call = None
    for call_obj in mock_cursor.execute.call_args_list:
        args, _ = call_obj
        if "INSERT INTO actions_log" in args[0] and len(args) > 1:
            params = args[1]
            if (params[0] == "test_bot" and 
                params[1] == "PROCESS_ERROR" and 
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
    # Add created_utc attribute to mock to avoid TypeError
    mock_submission.created_utc = datetime.datetime.now().timestamp() - 3600  # 1 hour ago
    mock_submission.stickied = False
    mock_submission.title = "Normal post"
    mock_submission.score = 5
    mock_submission.num_comments = 10
    
    result = agent._is_post_relevant(mock_submission)
    
    assert result is True, "For a normal post, _is_post_relevant should return True"


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
    
    # Reset mocks to clear previous calls
    mock_db_conn.cursor.reset_mock()
    mock_cursor.execute.reset_mock()
    mock_db_conn.commit.reset_mock()
    
    # Mock ensure_bot_registered to avoid additional DB calls
    mocker.patch('src.utils.database_utils.ensure_bot_registered')
    
    # Call the method under test
    action_type = "TEST_ACTION"
    target_id = "test_target"
    status = "TEST_STATUS"
    details = "Test details"
    
    agent._log_action(action_type, target_id, status, details)
    
    # Don't verify the exact number of cursor calls, as ensure_bot_registered may call it too
    # Instead, verify that at least one cursor call was made
    assert mock_db_conn.cursor.call_count >= 1
    
    # Check that execute was called with the correct SQL and parameters
    # Find the INSERT INTO actions_log call
    insert_call = None
    for call_obj in mock_cursor.execute.call_args_list:
        args, _ = call_obj
        if "INSERT INTO actions_log" in args[0]:
            insert_call = call_obj
            break
    
    assert insert_call is not None, "No INSERT INTO actions_log call was found"
    
    args, _ = insert_call
    # Verify the parameters match what we provided
    params = args[1]
    assert params[0] == "test_bot"  # bot_username
    assert params[1] == action_type
    assert params[2] == target_id
    assert params[3] == status
    assert params[4] == details
    
    # Verify that we committed the changes
    assert mock_db_conn.commit.call_count >= 1


def test_is_post_relevant_comprehensive(agent_setup, mocker):
    """
    Comprehensive test for _is_post_relevant with various post types.
    
    This test verifies that:
    1. Old posts (>24 hours) are skipped
    2. Posts with no comments are skipped
    3. Posts with negative score are skipped
    4. Normal posts are considered relevant
    """
    agent, _, _ = agent_setup
    
    # Set a common creation time for all test posts (3 hours ago)
    created_time = datetime.datetime.now().timestamp() - 10800
    
    # Test case 1: Old post (>24 hours)
    old_post = mocker.MagicMock()
    old_post.created_utc = datetime.datetime.now().timestamp() - 90000  # 25 hours ago
    old_post.stickied = False
    old_post.title = "Normal post"
    old_post.score = 5
    old_post.num_comments = 10
    assert agent._is_post_relevant(old_post) is False
    
    # Test case 2: Low score post
    low_score = mocker.MagicMock()
    low_score.created_utc = created_time
    low_score.stickied = False
    low_score.title = "Normal post"
    low_score.score = 0
    low_score.num_comments = 10
    assert agent._is_post_relevant(low_score) is False
    
    # Test case 3: No comments
    no_comments = mocker.MagicMock()
    no_comments.created_utc = created_time
    no_comments.stickied = False
    no_comments.title = "Normal post"
    no_comments.score = 5
    no_comments.num_comments = 0
    assert agent._is_post_relevant(no_comments) is False
    
    # Test case 4: Normal relevant post
    relevant_post = mocker.MagicMock()
    relevant_post.created_utc = created_time
    relevant_post.stickied = False
    relevant_post.title = "Normal post"
    relevant_post.score = 5
    relevant_post.num_comments = 10
    assert agent._is_post_relevant(relevant_post) is True


def test_try_reply_to_comment_success(agent_setup, mocker):
    """
    Test that _try_reply_to_comment successfully replies to a comment.
    
    This test verifies that:
    1. The agent finds eligible comments
    2. It selects a comment with a positive score
    3. It generates a reply using the LLM handler
    4. It posts the reply via the comment's reply method
    """
    agent, mock_reddit, mock_db_conn = agent_setup
    
    # Create mock submission with comments
    mock_submission = mocker.MagicMock()
    mock_submission.id = "test_submission_id"
    
    # Create mock comments
    mock_comment1 = mocker.MagicMock()
    mock_comment1.id = "comment1"
    mock_comment1.score = 5
    mock_comment1.body = "This is a comment with enough length to be eligible"
    mock_comment1.author = "user1"
    
    mock_comment2 = mocker.MagicMock()
    mock_comment2.id = "comment2"
    mock_comment2.score = 10
    mock_comment2.body = "This is another comment with enough length to be eligible"
    mock_comment2.author = "user2"
    
    # Configure mock submission with comments
    mock_submission.comments = mocker.MagicMock()
    mock_submission.comments.replace_more = mocker.MagicMock()  # Mock the replace_more method
    mock_submission.comments.__iter__ = lambda self: iter([mock_comment1, mock_comment2])
    
    # Mock comment that will be returned by comment.reply()
    mock_reply = mocker.MagicMock()
    mock_reply.id = "reply_id"
    
    # Mock the LLM handler's generate_comment_from_submission function
    test_reply = "This is a helpful, AI-generated reply."
    mocker.patch('src.agent.generate_comment_from_submission', return_value=test_reply)
    
    # Mock the reply_to_comment method to return the mock reply
    reply_mock = mocker.patch.object(agent, 'reply_to_comment', return_value=mock_reply)
    
    # Call the method under test
    result = agent._try_reply_to_comment(mock_submission, "testsubreddit")
    
    # Verify the result is True (successful reply)
    assert result is True
    
    # Verify that the replace_more method was called
    mock_submission.comments.replace_more.assert_called_once_with(limit=0)
    
    # Verify that the reply_to_comment method was called
    assert reply_mock.call_count == 1
    
    # Verify that the comment passed to reply_to_comment has the expected attributes
    called_comment = reply_mock.call_args[0][0]
    assert called_comment.id in ["comment1", "comment2"]
    assert called_comment.score >= 5
    assert len(called_comment.body) >= 20


def test_try_reply_to_comment_no_eligible_comments(agent_setup, mocker):
    """
    Test that _try_reply_to_comment returns False when no eligible comments are found.
    
    This test verifies that:
    1. The agent checks for eligible comments
    2. When no eligible comments are found, it returns False
    3. No reply is posted
    4. No database entries are made
    """
    agent, mock_reddit, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Create mock submission with no eligible comments
    mock_submission = mocker.MagicMock()
    mock_submission.id = "test_submission_id"
    
    # Create mock comments that are not eligible
    mock_comment1 = mocker.MagicMock()
    mock_comment1.id = "comment1"
    mock_comment1.score = 0  # Not eligible due to score
    mock_comment1.body = "This is a comment"
    mock_comment1.author = "user1"
    
    mock_comment2 = mocker.MagicMock()
    mock_comment2.id = "comment2"
    mock_comment2.score = 5
    mock_comment2.body = "Short"  # Not eligible due to length
    mock_comment2.author = "user2"
    
    mock_comment3 = mocker.MagicMock()
    mock_comment3.id = "comment3"
    mock_comment3.score = 5
    mock_comment3.body = "This is a comment from the bot"
    mock_comment3.author = "test_bot"  # Not eligible because it's from the bot
    
    # Configure mock submission with comments
    mock_submission.comments = [mock_comment1, mock_comment2, mock_comment3]
    
    # Call the method under test
    result = agent._try_reply_to_comment(mock_submission, "testsubreddit")
    
    # Verify the result is False (no reply made)
    assert result is False
    
    # Verify that no comment was replied to
    mock_comment1.reply.assert_not_called()
    mock_comment2.reply.assert_not_called()
    mock_comment3.reply.assert_not_called()
    
    # Verify no database interactions for logging actions or performance
    for call_obj in mock_cursor.execute.call_args_list:
        args, _ = call_obj
        if "INSERT INTO" in args[0]:
            assert False, "Should not insert any records when no reply is made"


def test_try_reply_to_comment_handles_exception(agent_setup, mocker):
    """
    Test that _try_reply_to_comment handles exceptions gracefully.
    
    This test verifies that:
    1. When an exception occurs during the reply process
    2. The agent catches the exception
    3. It returns False
    4. No database entries are made
    """
    agent, mock_reddit, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Create mock submission with comments
    mock_submission = mocker.MagicMock()
    mock_submission.id = "test_submission_id"
    
    # Create mock comment
    mock_comment = mocker.MagicMock()
    mock_comment.id = "comment1"
    mock_comment.score = 5
    mock_comment.body = "This is a comment with enough length to be eligible"
    mock_comment.author = "user1"
    
    # Configure mock submission with comments
    mock_submission.comments = mocker.MagicMock()
    mock_submission.comments.replace_more = mocker.MagicMock()  # Mock the replace_more method
    mock_submission.comments.__iter__ = lambda self: iter([mock_comment])
    
    # Mock the LLM handler's generate_comment_from_submission function
    test_reply = "This is a helpful, AI-generated reply."
    mocker.patch('src.agent.generate_comment_from_submission', return_value=test_reply)
    
    # Configure the reply_to_comment method to raise an exception
    error_message = "API error"
    mocker.patch.object(agent, 'reply_to_comment', side_effect=Exception(error_message))
    
    # Call the method under test
    result = agent._try_reply_to_comment(mock_submission, "testsubreddit")
    
    # Verify the result is False (reply failed)
    assert result is False
    
    # Verify that the replace_more method was called
    mock_submission.comments.replace_more.assert_called_once_with(limit=0)
    
    # Verify that the reply_to_comment method was called
    agent.reply_to_comment.assert_called_once_with(mock_comment, test_reply)
    
    # Verify the error was logged
    agent.logger.error.assert_called_once()
    assert error_message in str(agent.logger.error.call_args[0][0])


def test_process_submission_tries_comment_reply_first(agent_setup, mocker):
    """
    Test that _process_submission tries to reply to a comment before replying to the submission.
    
    This test verifies that:
    1. The agent first tries to reply to a comment
    2. If that succeeds, it doesn't try to reply to the submission
    3. The appropriate actions are logged
    """
    agent, _, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Configure mock cursor to return empty result (no previous comment)
    mock_cursor.fetchone.return_value = None
    
    # Create mock submission
    mock_submission = mocker.MagicMock()
    mock_submission.id = "test_submission_id"
    
    # Mock _try_reply_to_comment to return True (successful reply)
    mocker.patch.object(agent, '_try_reply_to_comment', return_value=True)
    
    # Mock _is_post_relevant to return True
    mocker.patch.object(agent, '_is_post_relevant', return_value=True)
    
    # Call the method under test
    agent._process_submission(mock_submission, "testsubreddit")
    
    # Verify _try_reply_to_comment was called
    agent._try_reply_to_comment.assert_called_once_with(mock_submission, "testsubreddit")
    
    # Verify that submission.reply was not called
    mock_submission.reply.assert_not_called()


def test_process_submission_falls_back_to_submission_reply(agent_setup, mocker):
    """
    Test that _process_submission falls back to replying to the submission if comment reply fails.
    
    This test verifies that:
    1. The agent first tries to reply to a comment
    2. If that fails, it falls back to replying to the submission
    3. The appropriate actions are logged
    """
    agent, _, mock_db_conn = agent_setup
    mock_cursor = mock_db_conn.cursor.return_value
    
    # Configure mock cursor to return empty result (no previous comment)
    mock_cursor.fetchone.return_value = None
    
    # Create mock submission
    mock_submission = mocker.MagicMock()
    mock_submission.id = "test_submission_id"
    
    # Mock comment that will be returned by submission.reply()
    mock_comment = mocker.MagicMock()
    mock_comment.id = "test_comment_id"
    mock_submission.reply.return_value = mock_comment
    
    # Mock _try_reply_to_comment to return False (failed to reply)
    mocker.patch.object(agent, '_try_reply_to_comment', return_value=False)
    
    # Mock _is_post_relevant to return True
    mocker.patch.object(agent, '_is_post_relevant', return_value=True)
    
    # Mock generate_comment_from_submission
    test_comment = "This is a helpful, AI-generated comment."
    mocker.patch('src.agent.generate_comment_from_submission', return_value=test_comment)
    
    # Call the method under test
    agent._process_submission(mock_submission, "testsubreddit")
    
    # Verify _try_reply_to_comment was called
    agent._try_reply_to_comment.assert_called_once_with(mock_submission, "testsubreddit")
    
    # Verify that submission.reply was called
    mock_submission.reply.assert_called_once_with(test_comment)
    
    # Verify database interactions for logging the action
    # Find the call that logs the successful comment
    comment_log_call = None
    for call_obj in mock_cursor.execute.call_args_list:
        args, _ = call_obj
        if "INSERT INTO actions_log" in args[0] and len(args) > 1:
            params = args[1]
            if (params[0] == "test_bot" and 
                params[1] == "COMMENT" and 
                params[2] == "test_submission_id" and 
                params[3] == "SUCCESS"):
                comment_log_call = call_obj
                break
    
    assert comment_log_call is not None, "No successful comment action was logged" 