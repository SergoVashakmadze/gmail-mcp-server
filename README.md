# Gmail MCP Server

A **Model Context Protocol (MCP)** server that enables AI assistants like Claude to read unread emails from your Gmail account and create draft replies.

![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 📧 **`get_unread_emails`** - Retrieve unread emails with sender, subject, body/snippet, and email/thread IDs
- ✉️ **`create_draft_reply`** - Create correctly threaded draft replies to emails
- 🔐 **OAuth 2.0 Authentication** - Secure Gmail API access
- 🔄 **Automatic Token Refresh** - Seamless credential management

## Prerequisites

- **Python 3.10+**
- **Gmail account** with API access enabled
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package manager (recommended)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/gmail-mcp-server.git
cd gmail-mcp-server
```

### 2. Install Dependencies

Using uv (recommended):
```bash
uv sync
```

Or with pip:
```bash
pip install -e .
```

### 3. Configure Gmail OAuth Credentials

Follow these steps to set up Gmail API access:

#### Step 3.1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click **"New Project"**
4. Enter a project name (e.g., "Gmail MCP Server")
5. Click **"Create"**

#### Step 3.2: Enable the Gmail API

1. In your project, go to **Navigation menu (≡) → APIs & Services → Library**
2. Search for **"Gmail API"**
3. Click on the Gmail API card
4. Click **"Enable"**

#### Step 3.3: Configure OAuth Consent Screen

1. Go to **APIs & Services → OAuth consent screen**
2. Select **"External"** user type (unless you have Google Workspace)
3. Fill in required information:
   - **App name**: "Gmail MCP Server"
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click **"Save and Continue"**
5. On the **Scopes** page, click **"Add or Remove Scopes"**
6. Add the following scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` (Read emails)
   - `https://www.googleapis.com/auth/gmail.compose` (Create drafts)
7. Click **"Save and Continue"**
8. Add your Gmail address as a **Test User**
9. Click **"Save and Continue"**

#### Step 3.4: Create OAuth Credentials

1. Go to **APIs & Services → Credentials**
2. Click **"Create Credentials" → "OAuth client ID"**
3. Select **"Desktop app"** as application type
4. Enter a name (e.g., "Gmail MCP Desktop")
5. Click **"Create"**
6. Click **"Download JSON"**
7. Save the file as `credentials.json` in your project root

### 4. Test Your Setup

Verify your OAuth configuration:

```bash
uv run python scripts/test_gmail_setup.py
```

This will:
- Check for your credentials file
- Run the OAuth flow (opens browser on first run)
- Test Gmail API access
- Save your token for future use

Expected output:
```
============================================================
Gmail OAuth Setup Test
============================================================

1. Checking for credentials file: credentials.json
   ✓ Credentials file found

2. Loading credentials...
   Starting OAuth flow (this will open your browser)...
   ✓ Token saved to token.json

3. Testing Gmail API access...
   ✓ Connected as: your.email@gmail.com
   Total messages: 1234

4. Testing message listing...
   ✓ Successfully retrieved 5 messages from inbox

5. Testing message retrieval...
   ✓ Sample email:
      From: sender@example.com...
      Subject: Example Subject...

6. Verifying draft creation scope...
   ✓ Draft creation scope is authorized

============================================================
✓ All tests passed! Your Gmail MCP server is ready to use.
============================================================
```

### 5. Run the Server

Development mode with MCP Inspector:
```bash
uv run mcp dev src/server.py
```

Or run directly:
```bash
uv run python src/server.py
```

## Claude Desktop Configuration

To connect Claude Desktop to your MCP server, edit your `claude_desktop_config.json`:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/gmail-mcp-server",
        "run",
        "python",
        "src/server.py"
      ],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/absolute/path/to/gmail-mcp-server/credentials.json",
        "GMAIL_TOKEN_PATH": "/absolute/path/to/gmail-mcp-server/token.json",
        "GMAIL_MAX_RESULTS": "10"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/gmail-mcp-server` with the actual path to your project directory.

### Alternative Configuration (Using npx)

If you prefer not to use uv:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": ["/absolute/path/to/gmail-mcp-server/src/server.py"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/absolute/path/to/credentials.json",
        "GMAIL_TOKEN_PATH": "/absolute/path/to/token.json"
      }
    }
  }
}
```

After saving the configuration, **restart Claude Desktop** to load the new MCP server.

## Available Tools

### `get_unread_emails`

Retrieve unread emails from your Gmail inbox.

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_results` | int | 10 | Maximum number of emails to retrieve |

**Returns:**
```json
{
  "count": 3,
  "emails": [
    {
      "message_id": "abc123",
      "thread_id": "thread456",
      "sender": "john@example.com",
      "subject": "Project Update",
      "snippet": "Hi, here's the latest update on...",
      "body": "Full email body text..."
    }
  ]
}
```

### `create_draft_reply`

Create a draft reply to an existing email, properly threaded in the conversation.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | str | Yes | The ID of the email to reply to |
| `thread_id` | str | Yes | The thread ID for proper threading |
| `reply_body` | str | Yes | The text content of the reply |
| `sender_email` | str | No | Override recipient email (defaults to original sender) |

**Returns:**
```json
{
  "success": true,
  "draft_id": "draft123",
  "message_id": "msg789",
  "thread_id": "thread456",
  "to": "john@example.com",
  "subject": "Re: Project Update",
  "message": "Draft reply created successfully. You can review and send it from Gmail."
}
```

### `get_email_details`

Get detailed information about a specific email.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | str | Yes | The ID of the email to retrieve |

## Example Prompts for Claude

Here are some example prompts to use with Claude Desktop:

### Reading Emails

> "Check my unread emails and summarize them for me."

> "Show me my latest 5 unread emails."

> "Do I have any unread emails from my manager?"

### Creating Draft Replies

> "Read my unread emails and draft a polite reply to the email from John about the project update."

> "Check my inbox. If there are any meeting requests, create draft replies accepting them."

> "Look at my unread emails and help me draft professional responses to each one."

### Combined Workflows

> "Go through my unread emails, summarize each one, and help me draft appropriate replies."

> "Check if I have any urgent emails that need a response today and draft replies for them."

## Demo Screenshots

### Claude Desktop with MCP Tools

When properly configured, you'll see the MCP tools indicator in Claude Desktop:

```
┌─────────────────────────────────────────────┐
│                                             │
│  [🔧 gmail]  ← MCP server indicator         │
│                                             │
│  You: Check my unread emails                │
│                                             │
│  Claude: I'll check your unread emails...   │
│  [Using: get_unread_emails]                 │
│                                             │
│  You have 3 unread emails:                  │
│  1. From: john@example.com                  │
│     Subject: Project Update                 │
│     ...                                     │
│                                             │
└─────────────────────────────────────────────┘
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GMAIL_CREDENTIALS_PATH` | `credentials.json` | Path to OAuth credentials file |
| `GMAIL_TOKEN_PATH` | `token.json` | Path to store OAuth token |
| `GMAIL_MAX_RESULTS` | `10` | Default max emails to retrieve |

## Project Structure

```
gmail-mcp-server/
├── src/
│   └── server.py          # Main MCP server implementation
├── scripts/
│   └── test_gmail_setup.py # OAuth setup verification script
├── screenshots/           # Demo screenshots (optional)
├── credentials.json       # Your OAuth credentials (not committed)
├── token.json            # OAuth token (not committed)
├── pyproject.toml        # Project configuration
├── README.md             # This file
├── .gitignore            # Git ignore rules
└── LICENSE               # MIT License
```

## Troubleshooting

### Common Issues

**"Error: spawn uv ENOENT" in Claude Desktop**

Update your `claude_desktop_config.json` to use the absolute path to uv:
```json
{
  "mcpServers": {
    "gmail": {
      "command": "/Users/username/.local/bin/uv",
      ...
    }
  }
}
```

Find your uv path with: `which uv` (macOS/Linux) or `where uv` (Windows)

**"Credentials file not found"**

Make sure you've downloaded OAuth credentials from Google Cloud Console and saved them as `credentials.json` in the project root.

**"Token refresh failed"**

Delete `token.json` and run `test_gmail_setup.py` again to re-authenticate.

**"Access denied" or scope errors**

1. Delete `token.json`
2. Ensure your OAuth consent screen has the correct scopes
3. Re-run the setup test to get a new token

### Viewing Logs

Check Claude Desktop logs for MCP server issues:

**macOS**: `~/Library/Logs/Claude/`  
**Windows**: `%APPDATA%\Claude\logs\`

## Security Best Practices

- ⚠️ **Never commit** `credentials.json` or `token.json` to version control
- 🔐 Store credentials in a secure location with appropriate permissions
- 👀 Review Google Cloud Console regularly for unusual activity
- 🔄 Revoke tokens if you suspect unauthorized access

## Development

### Running Tests

```bash
uv run pytest tests/
```

### Formatting & Linting

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check --fix .
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Gmail API](https://developers.google.com/gmail/api)
