#!/usr/bin/env python3
"""
Unit tests for the utility functions in src/utils.py
"""

import pytest
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError
from src.utils import check_shadowban


class TestCheckShadowban:
    """Test suite for the check_shadowban function."""
    
    def test_check_shadowban_is_banned(self, mocker):
        """
        Test that check_shadowban returns True when a user is shadowbanned.
        
        A shadowbanned user's profile returns a 404 status code.
        """
        # Create a mock response with 404 status code
        mock_response = mocker.Mock()
        mock_response.status_code = 404
        
        # Patch requests.get to return our mock response
        mocker.patch('requests.get', return_value=mock_response)
        
        # Call the function with a test username
        result = check_shadowban('shadowbanned_user')
        
        # Assert that the function correctly identifies a shadowbanned user
        assert result is True
    
    def test_check_shadowban_is_not_banned(self, mocker):
        """
        Test that check_shadowban returns False when a user is not shadowbanned.
        
        A normal user's profile returns a 200 status code.
        """
        # Create a mock response with 200 status code
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        
        # Patch requests.get to return our mock response
        mocker.patch('requests.get', return_value=mock_response)
        
        # Call the function with a test username
        result = check_shadowban('active_user')
        
        # Assert that the function correctly identifies a non-shadowbanned user
        assert result is False
    
    def test_check_shadowban_network_error(self, mocker):
        """
        Test that check_shadowban handles network errors gracefully.
        
        When a network error occurs, the function should return False as a safe default.
        """
        # Patch requests.get to raise a RequestException
        mocker.patch('requests.get', side_effect=RequestException("Network error"))
        
        # Call the function with a test username
        result = check_shadowban('some_user')
        
        # Assert that the function handles the error and returns False
        assert result is False
    
    def test_check_shadowban_timeout(self, mocker):
        """
        Test that check_shadowban handles timeout errors gracefully.
        
        When a timeout occurs, the function should return False as a safe default.
        """
        # Patch requests.get to raise a Timeout
        mocker.patch('requests.get', side_effect=Timeout("Request timed out"))
        
        # Call the function with a test username
        result = check_shadowban('some_user')
        
        # Assert that the function handles the timeout and returns False
        assert result is False
    
    def test_check_shadowban_connection_error(self, mocker):
        """
        Test that check_shadowban handles connection errors gracefully.
        
        When a connection error occurs, the function should return False as a safe default.
        """
        # Patch requests.get to raise a ConnectionError
        mocker.patch('requests.get', side_effect=ConnectionError("Connection failed"))
        
        # Call the function with a test username
        result = check_shadowban('some_user')
        
        # Assert that the function handles the connection error and returns False
        assert result is False
    
    def test_check_shadowban_invalid_username(self):
        """
        Test that check_shadowban raises a ValueError for invalid usernames.
        
        The function should validate that the username is a non-empty string.
        """
        # Test with empty string
        with pytest.raises(ValueError):
            check_shadowban('')
        
        # Test with None
        with pytest.raises(ValueError):
            check_shadowban(None)
    
    def test_check_shadowban_removes_prefix(self, mocker):
        """
        Test that check_shadowban properly handles usernames with 'u/' prefix.
        
        The function should remove the 'u/' prefix before making the request.
        """
        # Create a mock response
        mock_response = mocker.Mock()
        mock_response.status_code = 200
        
        # Set up the mock to capture the URL that was requested
        mock_get = mocker.patch('requests.get', return_value=mock_response)
        
        # Call the function with a username that has the 'u/' prefix
        check_shadowban('u/username')
        
        # Get the URL that was requested
        args, _ = mock_get.call_args
        requested_url = args[0]
        
        # Assert that the 'u/' prefix was removed
        assert requested_url == "https://www.reddit.com/user/username" 