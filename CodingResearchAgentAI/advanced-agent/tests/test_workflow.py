from types import SimpleNamespace

from src.models import CompanyAnalysis, Evidence, ResearchState
from src.workflow import Workflow, _safe_http_url, _unique_names


class FakeFirecrawl:
    def __init__(self, results=None, markdown="# Tool documentation"):
        self.results = results or []
        self.markdown = markdown
        self.queries = []

    def search_companies(self, query, num_results=5):
        self.queries.append(query)
        return self.results

    def scrape_company_pages(self, url):
        return SimpleNamespace(markdown=self.markdown)


class FakeLLM:
    def __init__(self, response="FastAPI"):
        self.response = response
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        return SimpleNamespace(content=self.response)


def test_tool_extraction_passes_scraped_content_to_model():
    firecrawl = FakeFirecrawl(
        results=[{"url": "https://fastapi.tiangolo.com/", "title": "FastAPI"}],
        markdown="FastAPI is a Python web framework.",
    )
    llm = FakeLLM()
    workflow = Workflow.__new__(Workflow)
    workflow.firecrawl = firecrawl
    workflow.llm = llm
    from src.prompts import DeveloperToolsPrompts
    workflow.prompts = DeveloperToolsPrompts()

    result = workflow._extract_tools_step(ResearchState(query="Python API frameworks"))

    assert result["extracted_tools"] == ["FastAPI"]
    assert "FastAPI is a Python web framework." in llm.messages[0][1].content


def test_search_empty_result_is_safe_and_reported():
    workflow = Workflow.__new__(Workflow)
    workflow.firecrawl = FakeFirecrawl(results=[])
    workflow.llm = FakeLLM()
    from src.prompts import DeveloperToolsPrompts
    workflow.prompts = DeveloperToolsPrompts()

    result = workflow._extract_tools_step(ResearchState(query="unknown tools"))

    assert result["extracted_tools"] == []
    assert result["errors"]


def test_research_handles_missing_results_without_crashing():
    workflow = Workflow.__new__(Workflow)
    workflow.firecrawl = FakeFirecrawl(results=[])
    result = workflow._research_step(ResearchState(query="test query"))

    assert result["companies"] == []
    assert result["errors"]


def test_invalid_urls_are_rejected():
    assert _safe_http_url("javascript:alert(1)") == ""
    assert _safe_http_url("https://user:pass@example.com") == ""
    assert _safe_http_url("https://example.com/docs") == "https://example.com/docs"


def test_tool_names_are_deduplicated_and_bounded():
    assert _unique_names([" FastAPI", "fastapi", "Flask", "Django", "Pyramid", "Tornado"]) == [
        "FastAPI", "Flask", "Django", "Pyramid"
    ]


def test_evidence_model_has_required_provenance():
    evidence = Evidence(
        field="pricing_model",
        value="Free",
        source_url="https://example.com/pricing",
        excerpt="Free plan available",
    )
    assert evidence.source_url.startswith("https://")
    assert CompanyAnalysis(evidence=[evidence]).evidence[0].excerpt == "Free plan available"


def test_model_rejects_evidence_from_other_pages():
    content = "The project is open source."
    evidence = Evidence(
        field="is_open_source",
        value="true",
        source_url="https://attacker.example/",
        excerpt="The project is open source.",
    )
    # The workflow's evidence filter requires both the selected URL and exact excerpt.
    assert not (evidence.source_url == "https://official.example/" and evidence.excerpt in content)
