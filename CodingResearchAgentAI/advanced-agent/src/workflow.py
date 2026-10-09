"""LangGraph research workflow with bounded calls and source-grounded claims."""
import json
import logging
import os
from typing import Any
from urllib.parse import urlparse

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from .firecrawl import FirecrawlService
from .models import CompanyAnalysis, CompanyInfo, Evidence, ResearchState
from .prompts import DeveloperToolsPrompts

logger = logging.getLogger(__name__)
MAX_TOOLS = 4
MAX_SEARCH_RESULTS = 5
MAX_PAGE_CHARS = 12000


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value or "")


def _result_markdown(result: Any) -> str:
    if isinstance(result, dict):
        return _text(result.get("markdown") or result.get("content"))
    return _text(getattr(result, "markdown", "") or getattr(result, "content", ""))


def _safe_http_url(value: Any) -> str:
    url = _text(value).strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return ""
    if parsed.username or parsed.password:
        return ""
    host = parsed.hostname.rstrip(".").casefold()
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal", ".localhost")):
        return ""
    try:
        import ipaddress
        if not ipaddress.ip_address(host).is_global:
            return ""
    except ValueError:
        pass
    return url


def _unique_names(names: list[str], limit: int = MAX_TOOLS) -> list[str]:
    seen: set[str] = set()
    clean: list[str] = []
    for raw in names:
        name = raw.strip().lstrip("-*•0123456789. ").strip()
        key = name.casefold()
        if name and len(name) <= 100 and key not in seen:
            seen.add(key)
            clean.append(name)
        if len(clean) >= limit:
            break
    return clean


class Workflow:
    def __init__(self, firecrawl: FirecrawlService | None = None, llm: Any | None = None):
        self.firecrawl = firecrawl or FirecrawlService()
        if llm is not None:
            self.llm = llm
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("Missing OPENAI_API_KEY environment variable")
            self.llm = ChatOpenAI(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                temperature=0.1,
                timeout=45,
                max_retries=2,
                api_key=api_key,
            )
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(ResearchState)
        graph.add_node("extract_tools", self._extract_tools_step)
        graph.add_node("research", self._research_step)
        graph.add_node("analyze", self._analyze_step)
        graph.set_entry_point("extract_tools")
        graph.add_edge("extract_tools", "research")
        graph.add_edge("research", "analyze")
        graph.add_edge("analyze", END)
        return graph.compile()

    def _extract_tools_step(self, state: ResearchState) -> dict[str, Any]:
        logger.info("Discovering tools for query")
        results = self.firecrawl.search_companies(
            f"{state.query} tools comparison alternatives",
            num_results=MAX_SEARCH_RESULTS,
        )
        chunks: list[str] = []
        for result in results[:MAX_SEARCH_RESULTS]:
            url = _safe_http_url(result.get("url", ""))
            if not url:
                continue
            scraped = self.firecrawl.scrape_company_pages(url)
            markdown = _result_markdown(scraped)
            if markdown:
                # Assignment is intentional: previously this expression discarded the content.
                chunks.append(f"Source URL: {url}\n{markdown[:2500]}")
        all_content = "\n\n--- SOURCE BOUNDARY ---\n\n".join(chunks)
        if not all_content:
            return {"extracted_tools": [], "search_results": results, "errors": ["No usable source content was retrieved during discovery."]}
        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query, all_content)),
        ]
        try:
            response = self.llm.invoke(messages)
            names = _unique_names(_text(getattr(response, "content", "")).splitlines())
            return {"extracted_tools": names, "search_results": results}
        except Exception:
            logger.exception("Tool extraction model call failed")
            return {"extracted_tools": [], "search_results": results, "errors": ["Tool extraction failed; research will use direct search."]}

    def _analyze_company_content(self, company_name: str, url: str, content: str) -> CompanyAnalysis:
        structured_llm = self.llm.with_structured_output(CompanyAnalysis)
        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name, url, content)),
        ]
        try:
            analysis = structured_llm.invoke(messages)
            if not isinstance(analysis, CompanyAnalysis):
                analysis = CompanyAnalysis.model_validate(analysis)
            # Model-generated evidence is accepted only when its URL and excerpt are verifiable.
            verified: list[Evidence] = []
            for item in analysis.evidence:
                if item.source_url == url and item.excerpt.strip() and item.excerpt.strip() in content:
                    verified.append(item)
            analysis.evidence = verified
            return analysis
        except Exception:
            logger.exception("Structured analysis failed for %s", company_name)
            return CompanyAnalysis(description="Analysis unavailable; no claims were verified.")

    def _research_step(self, state: ResearchState) -> dict[str, Any]:
        tool_names = _unique_names(list(state.extracted_tools or []))
        errors = list(state.errors or [])
        if not tool_names:
            logger.info("No extracted tools; falling back to direct search")
            results = self.firecrawl.search_companies(state.query, num_results=MAX_TOOLS)
            tool_names = _unique_names([
                _text(item.get("metadata", {}).get("title") or item.get("title") or "")
                for item in results
            ])
            if not results:
                errors.append("Search returned no results or the provider was unavailable.")
        companies: list[CompanyInfo] = []
        source_records: list[dict[str, Any]] = []
        for tool_name in tool_names:
            search_results = self.firecrawl.search_companies(
                f"{tool_name} official documentation pricing API",
                num_results=MAX_SEARCH_RESULTS,
            )
            if not search_results:
                errors.append(f"No search results for {tool_name}.")
                companies.append(CompanyInfo(name=tool_name, description="No source was retrieved.", research_status="source_unavailable"))
                continue

            # Prefer results whose title/domain mentions the product. Never call a result official
            # merely because the query contained the word "official".
            candidates: list[dict[str, Any]] = []
            key = "".join(ch for ch in tool_name.casefold() if ch.isalnum())
            for item in search_results:
                url = _safe_http_url(item.get("url", ""))
                if not url:
                    continue
                host = (urlparse(url).hostname or "").casefold()
                title = _text(item.get("metadata", {}).get("title") or item.get("title") or "").casefold()
                host_key = "".join(ch for ch in host.split(".")[-2] if ch.isalnum()) if "." in host else "".join(ch for ch in host if ch.isalnum())
                title_key = "".join(ch for ch in title if ch.isalnum())
                score = int(bool(key and key in host_key)) * 2 + int(bool(key and key in title_key))
                candidates.append({**item, "_url": url, "_score": score})
            if not candidates:
                errors.append(f"No valid HTTP(S) source for {tool_name}.")
                companies.append(CompanyInfo(name=tool_name, description="No valid source URL was found.", research_status="source_unavailable"))
                continue
            candidates.sort(key=lambda item: item["_score"], reverse=True)
            selected = candidates[0]
            url = selected["_url"]
            scraped = self.firecrawl.scrape_company_pages(url)
            content = _result_markdown(scraped)[:MAX_PAGE_CHARS]
            if not content:
                errors.append(f"Could not retrieve page content for {tool_name}.")
                companies.append(CompanyInfo(name=tool_name, website=url, description="Source page could not be read; attributes remain unknown.", research_status="scrape_failed"))
                continue

            analysis = self._analyze_company_content(tool_name, url, content)
            # Ensure all retained evidence is actually from this fetched page.
            company = CompanyInfo(
                name=tool_name,
                website=url,
                description=analysis.description or "No supported description extracted.",
                pricing_model=analysis.pricing_model or "Unknown",
                is_open_source=analysis.is_open_source,
                tech_stack=analysis.tech_stack,
                api_available=analysis.api_available,
                language_support=analysis.language_support,
                integration_capabilities=analysis.integration_capabilities,
                evidence=analysis.evidence,
                research_status="completed" if analysis.evidence else "unverified",
            )
            companies.append(company)
            source_records.append({"name": tool_name, "url": url, "evidence_count": len(analysis.evidence)})
        return {"companies": companies, "search_results": source_records, "errors": errors}

    def _analyze_step(self, state: ResearchState) -> dict[str, Any]:
        logger.info("Generating evidence-aware recommendations")
        company_data = json.dumps(
            [company.model_dump(mode="json") for company in state.companies],
            ensure_ascii=False,
            default=str,
        )
        if not state.companies:
            return {"analysis": "I could not retrieve usable sources, so I cannot make a reliable recommendation."}
        messages = [
            SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
            HumanMessage(content=self.prompts.recommendations_user(state.query, company_data)),
        ]
        try:
            response = self.llm.invoke(messages)
            return {"analysis": _text(getattr(response, "content", "")) or "No recommendation was generated."}
        except Exception:
            logger.exception("Recommendation generation failed")
            return {"analysis": "Recommendation generation failed. Review the source records above; no recommendation could be verified.", "errors": list(state.errors) + ["Recommendation generation failed."]}

    def run(self, query: str) -> ResearchState:
        query = query.strip()
        if not query:
            raise ValueError("Research query must not be empty")
        if len(query) > 1000:
            raise ValueError("Research query must be 1000 characters or fewer")
        final_state = self.workflow.invoke(ResearchState(query=query).model_dump())
        return ResearchState.model_validate(final_state)
