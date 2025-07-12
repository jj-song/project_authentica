#!/usr/bin/env python3
"""
Unit tests for the LLM Handler module in src/llm_handler.py
"""

import pytest
from unittest.mock import patch, MagicMock
from src.llm_handler import generate_comment, call_openai_api, clean_response


class TestLLMHandler:
    """Test suite for the LLM Handler module."""
    
    def test_create_basic_prompt(self):
        """Test that _create_basic_prompt correctly formats the title and body."""
        title = "Test Title"
        body = "Test Body"
        
        # Access the private function through the module
        import src.llm_handler
        prompt = src.llm_handler._create_basic_prompt(title, body)
        
        assert "Title: Test Title" in prompt
        assert "Content: Test Body" in prompt
        assert "helpful" in prompt.lower()
    
    @patch('src.llm_handler.OPENAI_API_KEY', None)
    def test_call_openai_api_no_key(self):
        """Test that call_openai_api returns a placeholder when no API key is available."""
        result = call_openai_api("Test prompt")
        assert "placeholder" in result.lower()
    
    @patch('src.llm_handler.OpenAI')
    def test_call_openai_api_success(self, mock_openai):
        """Test that call_openai_api correctly processes a successful API response."""
        # Mock the OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock the response
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is a test response"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Set a dummy API key for testing
        with patch('src.llm_handler.OPENAI_API_KEY', 'test_key'):
            result = call_openai_api("Test prompt")
        
        assert result == "This is a test response"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.llm_handler.OpenAI')
    def test_call_openai_api_error(self, mock_openai):
        """Test that call_openai_api correctly handles API errors."""
        # Mock the OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Set a dummy API key for testing
        with patch('src.llm_handler.OPENAI_API_KEY', 'test_key'):
            with pytest.raises(Exception):
                call_openai_api("Test prompt")
    
    def test_clean_response_normal(self):
        """Test that clean_response handles normal text correctly."""
        text = "This is a normal response"
        result = clean_response(text)
        assert result == text
    
    def test_clean_response_remove_disclaimers(self):
        """Test that clean_response removes AI disclaimers."""
        text = "As an AI language model, I would say this is a test.\nThis is more text."
        result = clean_response(text)
        assert "As an AI language model" not in result
        assert "This is more text" in result
    
    def test_clean_response_remove_code_blocks(self):
        """Test that clean_response removes markdown code blocks."""
        text = "Here is some code:\n```python\nprint('hello')\n```\nMore text."
        result = clean_response(text)
        assert "```" not in result
        assert "print('hello')" in result
        assert "More text" in result
    
    @patch('src.llm_handler.call_openai_api')
    def test_generate_comment_success(self, mock_api_call):
        """Test that generate_comment successfully processes API responses."""
        mock_api_call.return_value = "This is a generated comment"
        
        result = generate_comment("Test Title", "Test Body")
        
        assert result == "This is a generated comment"
        mock_api_call.assert_called_once()
    
    @patch('src.llm_handler.call_openai_api')
    def test_generate_comment_error(self, mock_api_call):
        """Test that generate_comment handles API errors gracefully."""
        mock_api_call.side_effect = Exception("API Error")
        
        result = generate_comment("Test Title", "Test Body")
        
        assert "Sorry" in result
        mock_api_call.assert_called_once() 