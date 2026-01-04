"""
Gmail MCP Server
================
A Model Context Protocol (MCP) server that allows AI assistants to read unread 
emails from a Gmail account and create draft replies.

Features:
- get_unread_emails: Retrieve unread emails with sender, subject, body snippet, and IDs
- create_draft_reply: Create a correctly threaded draft reply to an email
"""

import sys
print("Server starting...", file=sys.stderr)

import os
import base64
import logging
from email.mime.text import MIMEText
from typing import Optional
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gmail API scopes
# gmail.readonly - for reading emails
# gmail.compose - for creating drafts
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

# Environment variables for configuration
CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "token.json")
MAX_RESULTS = int(os.environ.get("GMAIL_MAX_RESULTS", "10"))


@dataclass
class EmailMessage:
    """Represents an email message."""
    message_id: str
    thread_id: str
    sender: str
    subject: str
    snippet: str
    body: str


def get_gmail_service():
    """
    Initialize and return an authenticated Gmail API service.
    
    Handles OAuth2 authentication flow:
    1. Try to load existing credentials from token file
    2. Refresh if expired
    3. Run OAuth flow if no valid credentials exist
    """
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Credentials file not found at {CREDENTIALS_PATH}. "
                    "Please download OAuth credentials from Google Cloud Console."
                )
            logger.info("Running OAuth flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())
            logger.info(f"Token saved to {TOKEN_PATH}")
    
    return build("gmail", "v1", credentials=creds)


def decode_email_body(payload: dict) -> str:
    """
    Extract and decode the email body from the message payload.
    Handles both simple and multipart messages.
    """
    body = ""
    
    if "body" in payload and payload["body"].get("data"):
        # Simple message with body data
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    elif "parts" in payload:
        # Multipart message - look for text/plain or text/html
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                if part["body"].get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                    break
            elif mime_type == "text/html" and not body:
                if part["body"].get("data"):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            elif "parts" in part:
                # Nested multipart
                body = decode_email_body(part)
                if body:
                    break
    
    return body


def get_header_value(headers: list, name: str) -> str:
    """Extract a header value by name from the headers list."""
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def parse_email_message(message: dict) -> EmailMessage:
    """Parse a Gmail API message into an EmailMessage object."""
    headers = message.get("payload", {}).get("headers", [])
    
    return EmailMessage(
        message_id=message["id"],
        thread_id=message["threadId"],
        sender=get_header_value(headers, "From"),
        subject=get_header_value(headers, "Subject"),
        snippet=message.get("snippet", ""),
        body=decode_email_body(message.get("payload", {})),
    )


# Initialize the MCP server
mcp = FastMCP(
    "Gmail MCP Server",
    dependencies=["google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client"],
)


@mcp.tool()
def get_unread_emails(max_results: int = MAX_RESULTS) -> dict:
    """
    Retrieve unread emails from the Gmail inbox.
    
    Returns a list of emails with:
    - message_id: Unique identifier for the email
    - thread_id: Thread identifier for replies
    - sender: Email sender (From header)
    - subject: Email subject line
    - snippet: Brief preview of the email content
    - body: Full email body text
    
    Args:
        max_results: Maximum number of emails to retrieve (default: 10)
    
    Returns:
        List of dictionaries containing email details
    """
    try:
        service = get_gmail_service()
        
        # Search for unread messages in inbox
        results = service.users().messages().list(
            userId="me",
            q="is:unread in:inbox",
            maxResults=max_results,
        ).execute()
        
        messages = results.get("messages", [])
        
        if not messages:
            return {"message": "No unread emails found", "emails": []}
        
        emails = []
        for msg in messages:
            # Get full message details
            full_message = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full",
            ).execute()
            
            email = parse_email_message(full_message)
            emails.append({
                "message_id": email.message_id,
                "thread_id": email.thread_id,
                "sender": email.sender,
                "subject": email.subject,
                "snippet": email.snippet,
                "body": email.body[:2000] if len(email.body) > 2000 else email.body,  # Limit body size
            })
        
        return {
            "count": len(emails),
            "emails": emails,
        }
    
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        return {"error": f"Gmail API error: {e.reason}"}
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        return {"error": str(e)}


@mcp.tool()
def create_draft_reply(
    message_id: str,
    thread_id: str,
    reply_body: str,
    sender_email: Optional[str] = None,
) -> dict:
    """
    Create a draft reply to an existing email.
    
    The draft will be correctly threaded with the original conversation.
    
    Args:
        message_id: The ID of the email to reply to
        thread_id: The thread ID for proper threading
        reply_body: The text content of the reply
        sender_email: Optional sender email for the "To" field. 
                      If not provided, will be extracted from the original message.
    
    Returns:
        Dictionary with draft details including draft_id and message_id
    """
    try:
        service = get_gmail_service()
        
        # Get the original message to extract headers
        original = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()
        
        headers = original.get("payload", {}).get("headers", [])
        original_subject = get_header_value(headers, "Subject")
        original_from = get_header_value(headers, "From")
        original_message_id = get_header_value(headers, "Message-ID")
        
        # Determine the recipient
        to_address = sender_email if sender_email else original_from
        
        # Create reply subject (add Re: if not present)
        if original_subject.lower().startswith("re:"):
            reply_subject = original_subject
        else:
            reply_subject = f"Re: {original_subject}"
        
        # Create the MIME message
        message = MIMEText(reply_body)
        message["to"] = to_address
        message["subject"] = reply_subject
        
        # Add threading headers
        if original_message_id:
            message["In-Reply-To"] = original_message_id
            message["References"] = original_message_id
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        
        # Create the draft with proper threading
        draft_body = {
            "message": {
                "raw": raw_message,
                "threadId": thread_id,
            }
        }
        
        draft = service.users().drafts().create(
            userId="me",
            body=draft_body,
        ).execute()
        
        logger.info(f"Draft created successfully: {draft['id']}")
        
        return {
            "success": True,
            "draft_id": draft["id"],
            "message_id": draft["message"]["id"],
            "thread_id": thread_id,
            "to": to_address,
            "subject": reply_subject,
            "message": "Draft reply created successfully. You can review and send it from Gmail.",
        }
    
    except HttpError as e:
        logger.error(f"Gmail API error creating draft: {e}")
        return {"success": False, "error": f"Gmail API error: {e.reason}"}
    except Exception as e:
        logger.error(f"Error creating draft: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_email_details(message_id: str) -> dict:
    """
    Get detailed information about a specific email.
    
    Args:
        message_id: The ID of the email to retrieve
    
    Returns:
        Dictionary with full email details
    """
    try:
        service = get_gmail_service()
        
        message = service.users().messages().get(
            userId="me",
            id=message_id,
            format="full",
        ).execute()
        
        email = parse_email_message(message)
        headers = message.get("payload", {}).get("headers", [])
        
        return {
            "message_id": email.message_id,
            "thread_id": email.thread_id,
            "sender": email.sender,
            "to": get_header_value(headers, "To"),
            "cc": get_header_value(headers, "Cc"),
            "subject": email.subject,
            "date": get_header_value(headers, "Date"),
            "body": email.body,
        }
    
    except HttpError as e:
        logger.error(f"Gmail API error: {e}")
        return {"error": f"Gmail API error: {e.reason}"}
    except Exception as e:
        logger.error(f"Error fetching email: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    try:
        print("Running MCP server...", file=sys.stderr)
        mcp.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)