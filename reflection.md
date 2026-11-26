# Reflection

## 1. What did we ask the agent?

I asked the agent to build an MCP server connecting Gmail and Google Calendar to Antigravity. The goal was to manage emails, create drafts, schedule meetings, and find available time slots using natural language.

## 2. How did we check that the result is correct?

I tested the six tools using a real Google account and checked the results in Gmail and Google Calendar. I also ran 65 successful automated tests, checked scheduling conflicts, and tested how the agent handles malicious instructions in emails.

## 3. Which tool did we leave out, and why?

I decided not to include an automatic email-sending tool because I wanted the user to remain in control. Creating drafts instead of sending emails reduces mistakes and security risks.

## 4. L06 vs L07: What changed?

In L06, the Python application performed predefined tasks. In L07, the AI agent can understand natural-language requests and choose the appropriate MCP tools.

I learned how to make an AI system more flexible while maintaining security and human control.
