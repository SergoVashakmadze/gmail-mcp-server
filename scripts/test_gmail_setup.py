#!/usr/bin/env python3
"""
Gmail OAuth Setup Test Script
==============================
Run this script to verify your Gmail OAuth configuration is working correctly.

Usage:
    python scripts/test_gmail_setup.py

This will:
1. Load your OAuth credentials
2. Run the OAuth flow (opens browser on first run)
3. Test listing emails from your inbox
4. Save the token for future use
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes (must match server.py)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

# Configuration
CREDENTIALS_PATH = os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.environ.get("GMAIL_TOKEN_PATH", "token.json")


def main():
    print("=" * 60)
    print("Gmail OAuth Setup Test")
    print("=" * 60)
    
    # Check for credentials file
    print(f"\n1. Checking for credentials file: {CREDENTIALS_PATH}")
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"   ❌ ERROR: Credentials file not found at {CREDENTIALS_PATH}")
        print("\n   To fix this:")
        print("   1. Go to Google Cloud Console (https://console.cloud.google.com)")
        print("   2. Create a new project or select existing one")
        print("   3. Enable the Gmail API")
        print("   4. Configure OAuth consent screen")
        print("   5. Create OAuth 2.0 credentials (Desktop app)")
        print("   6. Download the JSON file and save as 'credentials.json'")
        return False
    print("   ✓ Credentials file found")
    
    # Load or create credentials
    print(f"\n2. Loading credentials...")
    creds = None
    
    if os.path.exists(TOKEN_PATH):
        print(f"   Found existing token at {TOKEN_PATH}")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("   Token expired, refreshing...")
            creds.refresh(Request())
        else:
            print("   Starting OAuth flow (this will open your browser)...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
        print(f"   ✓ Token saved to {TOKEN_PATH}")
    else:
        print("   ✓ Using valid existing token")
    
    # Test Gmail API access
    print("\n3. Testing Gmail API access...")
    try:
        service = build("gmail", "v1", credentials=creds)
        
        # Get user profile
        profile = service.users().getProfile(userId="me").execute()
        print(f"   ✓ Connected as: {profile['emailAddress']}")
        print(f"   Total messages: {profile.get('messagesTotal', 'N/A')}")
        
        # List some messages
        print("\n4. Testing message listing...")
        results = service.users().messages().list(
            userId="me",
            maxResults=5,
            q="in:inbox"
        ).execute()
        
        messages = results.get("messages", [])
        print(f"   ✓ Successfully retrieved {len(messages)} messages from inbox")
        
        if messages:
            # Get first message details
            print("\n5. Testing message retrieval...")
            msg = service.users().messages().get(
                userId="me",
                id=messages[0]["id"],
                format="metadata",
                metadataHeaders=["Subject", "From"]
            ).execute()
            
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            print(f"   ✓ Sample email:")
            print(f"      From: {headers.get('From', 'N/A')[:50]}...")
            print(f"      Subject: {headers.get('Subject', 'N/A')[:50]}...")
        
        # Test draft creation capability
        print("\n6. Verifying draft creation scope...")
        # Just verify the scope is present, don't actually create a draft
        if "https://www.googleapis.com/auth/gmail.compose" in creds.scopes:
            print("   ✓ Draft creation scope is authorized")
        else:
            print("   ⚠ Draft creation scope may not be authorized")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed! Your Gmail MCP server is ready to use.")
        print("=" * 60)
        return True
        
    except HttpError as error:
        print(f"   ❌ Gmail API Error: {error}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
