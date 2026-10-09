# Simple MCP Agent

A minimal interactive agent using LangGraph, OpenAI, and the Firecrawl MCP server.

## Requirements

- Python 3.11+
- Node.js/npm (provides `npx`)
- OpenAI API key
- Firecrawl API key

## Setup

From this directory:

```bash
uv sync
```

Create a `.env` file in `simple-agent/`:

```dotenv
OPENAI_API_KEY=...
FIRECRAWL_API_KEY=...
# Optional:
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

Run it:

```bash
uv run python main.py
```

Enter a question and type `quit` or `exit` to stop. Inputs are capped at 12,000 characters and the recent conversation window is bounded to control context growth. Retrieved webpages are untrusted input; always independently verify important claims.

## Safety notes

The model can invoke tools exposed by the configured MCP server. Only use a trusted server configuration and a restricted Firecrawl key. Do not expose credentials in prompts or logs. This sample does not implement a human approval workflow for arbitrary third-party MCP tools; do not add privileged tools without server-side authorization and explicit confirmation.
