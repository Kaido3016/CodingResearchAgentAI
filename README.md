# CodingResearchAgentAI

An experimental developer-tools research project with two separate entry points: an evidence-aware LangGraph workflow and a lightweight MCP-powered Firecrawl assistant.

**Stack:** Python 3.11+, LangGraph, LangChain, OpenAI (default model: `gpt-4o-mini`), Firecrawl, Pydantic, Model Context Protocol (MCP).

## Components

- **Advanced agent** (`CodingResearchAgentAI/advanced-agent`): searches and scrapes pages, extracts tool names, records structured attributes, filters model-generated evidence to excerpts actually present in the selected page, and generates cautious recommendations.
- **Simple MCP agent** (`CodingResearchAgentAI/simple-agent`): interactive assistant using the Firecrawl MCP server through `npx`, with input and conversation-history bounds.

## Quick start: advanced agent

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/), an OpenAI API key, and a Firecrawl API key.

```bash
cd CodingResearchAgentAI/advanced-agent
uv sync --extra dev
```

Create a `.env` file in this directory:

```dotenv
OPENAI_API_KEY=your_openai_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
# Optional:
OPENAI_MODEL=gpt-4o-mini
```

Run the CLI:

```bash
uv run python main.py
```

## Quick start: simple MCP agent

Prerequisites: Python 3.11+, Node.js/npm (for `npx`), OpenAI API key, and Firecrawl API key.

```bash
cd CodingResearchAgentAI/simple-agent
uv sync
```

Create a `.env` file in `simple-agent/` with `OPENAI_API_KEY` and `FIRECRAWL_API_KEY`, then run:

```bash
uv run python main.py
```

Type `quit` or `exit` to stop either CLI.

## Reliability and security notes

- Search failures produce empty results and warnings instead of inconsistent return types.
- Research attributes should be treated as unverified unless there is claim-level evidence with an excerpt that exactly matches the selected source page.
- Retrieved pages are untrusted input. Prompt boundaries help but do not eliminate prompt-injection risk.
- A search result is not guaranteed to be the product's official website. Review source URLs before relying on findings.
- External pricing and feature information can change. Independently verify consequential decisions.
- The simple agent can invoke tools exposed by its MCP server. Use only trusted MCP servers and least-privilege API keys; this sample does not implement approval for arbitrary privileged tools.

## Development

Advanced-agent tests and linting:

```bash
cd CodingResearchAgentAI/advanced-agent
uv sync --extra dev
uv run ruff check src tests main.py
uv run pytest --cov=src --cov-report=term-missing
```

GitHub Actions runs lint/tests for the advanced agent and a compile check for the simple agent. No live API calls are needed by the unit tests.

## Project layout

```text
.
├── .github/workflows/ci.yml
├── LICENSE
├── README.md
└── CodingResearchAgentAI
    ├── advanced-agent
    │   ├── main.py
    │   ├── pyproject.toml
    │   ├── src
    │   └── tests
    ├── simple-agent
    │   ├── main.py
    │   └── pyproject.toml
    └── requirements.txt
```

## License

MIT. See [LICENSE](LICENSE).
