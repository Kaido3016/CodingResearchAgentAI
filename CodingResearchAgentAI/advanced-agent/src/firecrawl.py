"""Typed, failure-tolerant wrapper around the Firecrawl SDK."""
import ipaddress
import logging
import os
from typing import Any
from urllib.parse import urlparse

from dotenv import load_dotenv
from firecrawl import FirecrawlApp, ScrapeOptions

load_dotenv()
logger = logging.getLogger(__name__)


def _as_mapping(value: Any) -> dict[str, Any]:
    """Normalize SDK result objects and dictionaries to plain mappings."""
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            pass
    if hasattr(value, "dict"):
        try:
            return value.dict()
        except Exception:
            pass
    return {}


def _safe_public_url(value: str) -> bool:
    """Reject malformed URLs, credentials, local hostnames, and literal non-public IPs."""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False
    host = parsed.hostname.rstrip(".").casefold()
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal", ".localhost")):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return address.is_global


class FirecrawlService:
    def __init__(self, app: Any | None = None):
        api_key = os.getenv("FIRECRAWL_API_KEY")
        if app is None and not api_key:
            raise ValueError("Missing FIRECRAWL_API_KEY environment variable")
        self.app = app if app is not None else FirecrawlApp(api_key=api_key)

    def search_companies(self, query: str, num_results: int = 5) -> list[dict[str, Any]]:
        """Return a consistent list on success, empty results, and provider errors."""
        if not query.strip():
            return []
        try:
            result = self.app.search(
                query=query,
                limit=max(1, min(int(num_results), 10)),
                scrape_options=ScrapeOptions(formats=["markdown"]),
            )
            items = getattr(result, "data", None)
            if items is None and isinstance(result, dict):
                items = result.get("data", [])
            normalized: list[dict[str, Any]] = []
            for item in items or []:
                entry = _as_mapping(item)
                if entry:
                    normalized.append(entry)
            return normalized
        except Exception:
            logger.exception("Firecrawl search failed for query %r", query)
            return []

    def scrape_company_pages(self, url: str) -> Any | None:
        """Scrape public HTTP(S) URLs only; return None on a provider failure."""
        if not _safe_public_url(url):
            logger.warning("Refusing to scrape an invalid or non-public URL: %r", url)
            return None
        try:
            return self.app.scrape_url(url, formats=["markdown"])
        except Exception:
            logger.exception("Firecrawl scrape failed for URL %r", url)
            return None
