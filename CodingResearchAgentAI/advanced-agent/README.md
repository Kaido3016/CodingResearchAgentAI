# Advanced Developer Tools Research Agent

A CLI research assistant built with LangGraph, LangChain, Firecrawl, OpenAI, and Pydantic. It discovers developer tools, extracts structured attributes, retains claim-level evidence, and produces cautious recommendations.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- OpenAI API key
- Firecrawl API key

## Setup

From this directory:

```bash
uv sync --extra dev
```

Create a `.env` file in this directory:

```dotenv
OPENAI_API_KEY=your_openai_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
# Optional:
OPENAI_MODEL=gpt-4o-mini
```

Run:

```bash
uv run python main.py
```

Type `quit` or `exit` to stop.

## Workflow

1. Search for relevant articles and scrape valid HTTP(S) source URLs.
2. Extract up to four distinct product names.
3. Search for each tool, choose a candidate source, and scrape its content.
4. Extract structured attributes with claim-level evidence.
5. Keep evidence only when its source URL matches the selected page and the excerpt is present verbatim in retrieved content.
6. Generate recommendations while surfacing missing evidence and search/scrape warnings.

## Important limitations

- Search-result ranking is heuristic. A result returned for an “official” query is not guaranteed to be an official source.
- Evidence excerpt matching improves traceability but is not a semantic fact-check and cannot guarantee a claim is true.
- Prompt-injection boundaries are defense-in-depth, not a complete security guarantee.
- The project makes live OpenAI and Firecrawl calls at runtime; unit tests use fakes and do not certify live-provider behavior.
- Do not treat generated pricing or feature claims as authoritative without reviewing the cited source.

## Tests

```bash
uv run ruff check src tests main.py
uv run pytest --cov=src --cov-report=term-missing
```

## Configuration

The model defaults to `gpt-4o-mini`. Override it with `OPENAI_MODEL`. API keys are read from environment variables or a local `.env` file and must never be committed.
