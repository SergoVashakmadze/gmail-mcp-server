# Example Prompts for Gmail MCP Server

This document provides example prompts you can use with Claude Desktop once the Gmail MCP server is configured.

## Basic Email Reading

### Check Unread Emails
```
Check my unread emails and give me a summary.
```

### Specific Number of Emails
```
Show me my latest 5 unread emails.
```

### Detailed Email View
```
Look at my unread emails and show me the full details of each one.
```

## Creating Draft Replies

### Simple Reply
```
I have an email from John about the project deadline. 
Draft a polite reply saying I'll have the report ready by Friday.
```

### Professional Response
```
Check my unread emails. If there's anything from my manager, 
draft a professional response acknowledging their message.
```

### Multiple Drafts
```
Go through all my unread emails and create draft replies 
for each one. Keep the tone professional but friendly.
```

## Combined Workflows

### Triage and Respond
```
Triage my unread emails:
1. Show me a summary of each
2. Identify which ones need urgent responses
3. Draft replies for the urgent ones
```

### Meeting Responses
```
Look for any meeting invitation emails in my inbox. 
For each one, create a draft reply accepting the meeting.
```

### Follow-up Emails
```
Check if I have any emails that look like they need a follow-up response.
Help me draft appropriate replies.
```

## Advanced Prompts

### Summarize by Sender
```
Group my unread emails by sender and give me a summary 
of what each person is writing about.
```

### Priority Analysis
```
Analyze my unread emails and rank them by importance:
- High: Needs immediate response
- Medium: Can respond within 24 hours
- Low: Can respond when convenient

Then draft responses for the high-priority ones.
```

### Context-Aware Replies
```
I'm working on the Q4 marketing campaign. 
Look for any emails related to marketing or campaigns 
and draft replies that reference our Q4 goals.
```

## Tips for Best Results

1. **Be Specific**: Tell Claude exactly what you want in the reply
2. **Provide Context**: Give background information when needed
3. **Set Tone**: Specify if you want formal, casual, friendly, etc.
4. **Request Review**: Always review drafts before sending them

## Example Conversation

**You**: Check my unread emails

**Claude**: I'll check your unread emails now.
*[Uses get_unread_emails tool]*

You have 3 unread emails:

1. **From**: john.smith@company.com
   **Subject**: Q4 Budget Review Meeting
   **Preview**: Hi, I'd like to schedule a meeting to discuss...

2. **From**: marketing@newsletter.com
   **Subject**: Your Weekly Digest
   **Preview**: Here's what happened this week...

3. **From**: sarah.jones@client.com
   **Subject**: Proposal Feedback
   **Preview**: Thank you for sending the proposal. I have a few...

Would you like me to draft replies to any of these?

**You**: Draft a reply to Sarah's email saying thank you and that I'll address her feedback by end of week

**Claude**: I'll create a draft reply to Sarah's email.
*[Uses create_draft_reply tool]*

Done! I've created a draft reply with the following content:

---
**To**: sarah.jones@client.com
**Subject**: Re: Proposal Feedback

Dear Sarah,

Thank you for taking the time to review the proposal and share your feedback. I appreciate your thoughtful comments.

I'll address each of your points and have a revised proposal ready by the end of this week. If you have any additional thoughts in the meantime, please don't hesitate to reach out.

Best regards
---

The draft is saved in your Gmail drafts folder. Would you like me to make any changes before you send it?
