---
name: boldsign-assistant
description: Uses the BoldSign Assistant MCP tool for BoldSign eSignature API help. Use when the user invokes /boldsign-assistant, asks about BoldSign APIs, integration, webhooks, signature workflows, or e-signature implementation.
---

# BoldSign Assistant

## When to Use

Apply this skill when the user:
- Invokes `/boldsign-assistant` or `/boldsign`
- Asks about BoldSign eSignature APIs, endpoints, or integration
- Needs help with signature requests, templates, webhooks, or document workflows
- References `@boldsign` or `@ask_boldsign`

## How to Use

1. **Extract the query** from the user's message. If they only invoked the command, ask what they need help with or infer from recent context.

2. **Call the MCP tool** with `call_mcp_tool`:
   - `server`: `"user-boldsign-assistant"`
   - `toolName`: `"BoldSignAssistant"`
   - `arguments`: `{ "query": "<the user's question or topic>" }`

3. **Use the response** to answer the user. The tool returns documentation references and implementation guidance.

## Example

User: `/boldsign-assistant How do I send a document for signature via the API?`

```
call_mcp_tool(
  server: "user-boldsign-assistant",
  toolName: "BoldSignAssistant",
  arguments: { "query": "How do I send a document for signature via the API?" }
)
```

## Notes

- The `query` argument is required. Be specific—include API names, workflows, or error context when relevant.
- The tool covers: Signature Requests, Templates, Audit Logs, Reminders, Access Codes, webhooks, signer management, and SDK usage.
