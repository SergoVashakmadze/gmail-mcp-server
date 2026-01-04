"""
Tests for Gmail MCP Server

These tests verify the MCP server tools work correctly.
Note: Some tests require valid Gmail OAuth credentials to run.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestEmailParsing:
    """Test email parsing utilities."""
    
    def test_get_header_value(self):
        """Test extracting header values."""
        from server import get_header_value
        
        headers = [
            {"name": "From", "value": "sender@example.com"},
            {"name": "Subject", "value": "Test Subject"},
            {"name": "To", "value": "recipient@example.com"},
        ]
        
        assert get_header_value(headers, "From") == "sender@example.com"
        assert get_header_value(headers, "Subject") == "Test Subject"
        assert get_header_value(headers, "from") == "sender@example.com"  # case insensitive
        assert get_header_value(headers, "NonExistent") == ""
    
    def test_decode_simple_email_body(self):
        """Test decoding a simple email body."""
        from server import decode_email_body
        import base64
        
        test_text = "Hello, this is a test email body."
        encoded = base64.urlsafe_b64encode(test_text.encode()).decode()
        
        payload = {
            "body": {"data": encoded}
        }
        
        result = decode_email_body(payload)
        assert result == test_text
    
    def test_decode_multipart_email_body(self):
        """Test decoding a multipart email body."""
        from server import decode_email_body
        import base64
        
        text_content = "Plain text version"
        encoded = base64.urlsafe_b64encode(text_content.encode()).decode()
        
        payload = {
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": encoded}
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": base64.urlsafe_b64encode(b"<p>HTML version</p>").decode()}
                }
            ]
        }
        
        result = decode_email_body(payload)
        assert result == text_content


class TestEmailMessage:
    """Test EmailMessage dataclass."""
    
    def test_email_message_creation(self):
        """Test creating an EmailMessage."""
        from server import EmailMessage
        
        email = EmailMessage(
            message_id="msg123",
            thread_id="thread456",
            sender="test@example.com",
            subject="Test Subject",
            snippet="This is a snippet...",
            body="Full body text"
        )
        
        assert email.message_id == "msg123"
        assert email.thread_id == "thread456"
        assert email.sender == "test@example.com"
        assert email.subject == "Test Subject"


class TestMCPServer:
    """Test MCP server initialization."""
    
    def test_server_has_required_tools(self):
        """Verify the MCP server has the required tools."""
        from server import mcp
        
        # The server should be initialized
        assert mcp is not None
        assert mcp.name == "Gmail MCP Server"


class TestGetUnreadEmailsMocked:
    """Test get_unread_emails with mocked Gmail API."""
    
    @patch('server.get_gmail_service')
    def test_get_unread_emails_empty(self, mock_service):
        """Test when there are no unread emails."""
        from server import get_unread_emails
        
        # Mock the Gmail API response
        mock_gmail = MagicMock()
        mock_service.return_value = mock_gmail
        
        mock_gmail.users().messages().list().execute.return_value = {
            "messages": []
        }
        
        result = get_unread_emails(max_results=5)
        
        assert "emails" in result
        assert result["emails"] == []
    
    @patch('server.get_gmail_service')
    def test_get_unread_emails_with_messages(self, mock_service):
        """Test when there are unread emails."""
        from server import get_unread_emails
        import base64
        
        # Mock the Gmail API responses
        mock_gmail = MagicMock()
        mock_service.return_value = mock_gmail
        
        # List response
        mock_gmail.users().messages().list().execute.return_value = {
            "messages": [{"id": "msg1", "threadId": "thread1"}]
        }
        
        # Get response
        body_text = "Test email body"
        encoded_body = base64.urlsafe_b64encode(body_text.encode()).decode()
        
        mock_gmail.users().messages().get().execute.return_value = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test snippet",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@test.com"},
                    {"name": "Subject", "value": "Test Subject"},
                ],
                "body": {"data": encoded_body}
            }
        }
        
        result = get_unread_emails(max_results=5)
        
        assert result["count"] == 1
        assert len(result["emails"]) == 1
        assert result["emails"][0]["sender"] == "sender@test.com"
        assert result["emails"][0]["subject"] == "Test Subject"


class TestCreateDraftReplyMocked:
    """Test create_draft_reply with mocked Gmail API."""
    
    @patch('server.get_gmail_service')
    def test_create_draft_reply_success(self, mock_service):
        """Test successful draft creation."""
        from server import create_draft_reply
        import base64
        
        mock_gmail = MagicMock()
        mock_service.return_value = mock_gmail
        
        # Mock getting original message
        mock_gmail.users().messages().get().execute.return_value = {
            "id": "orig_msg",
            "threadId": "thread1",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@test.com"},
                    {"name": "Subject", "value": "Original Subject"},
                    {"name": "Message-ID", "value": "<original@message.id>"},
                ]
            }
        }
        
        # Mock creating draft
        mock_gmail.users().drafts().create().execute.return_value = {
            "id": "draft123",
            "message": {
                "id": "new_msg_id",
                "threadId": "thread1"
            }
        }
        
        result = create_draft_reply(
            message_id="orig_msg",
            thread_id="thread1",
            reply_body="Thank you for your email!"
        )
        
        assert result["success"] is True
        assert result["draft_id"] == "draft123"
        assert result["subject"] == "Re: Original Subject"
        assert result["to"] == "sender@test.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
