from types import SimpleNamespace

from src.models import CompanyAnalysis, Evidence, ResearchState
from src.prompts import DeveloperToolsPrompts
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
    def __init__(self, response="FastAPI", structured_response=None):
        self.response = response
        self.structured_response = structured_response
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        return SimpleNamespace(content=self.response)

    def with_structured_output(self, schema):
        return FakeStructuredLLM(self.structured_response or schema())


class FakeStructuredLLM:
    def __init__(self, response):
        self.response = response

    def invoke(self, messages):
        return self.response


def test_tool_extraction_passes_scraped_content_to_model():
    firecrawl = FakeFirecrawl(
        results=[{"url": "https://fastapi.tiangolo.com/", "title": "FastAPI"}],
        markdown="FastAPI is a Python web framework.",
    )
    llm = FakeLLM()
    workflow = Workflow.__new__(Workflow)
    workflow.firecrawl = firecrawl
    workflow.llm = llm
    workflow.prompts = DeveloperToolsPrompts()

    result = workflow._extract_tools_step(ResearchState(query="Python API frameworks"))

    assert result["extracted_tools"] == ["FastAPI"]
    assert "FastAPI is a Python web framework." in llm.messages[0][1].content


def test_search_empty_result_is_safe_and_reported():
    workflow = Workflow.__new__(Workflow)
    workflow.firecrawl = FakeFirecrawl(results=[])
    workflow.llm = FakeLLM()
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


def test_workflow_discards_evidence_not_matching_selected_source():
    content = "The project is open source."
    fake_analysis = CompanyAnalysis(
        is_open_source=True,
        evidence=[
            Evidence(
                field="is_open_source",
                value="true",
                source_url="https://attacker.example/",
                excerpt="The project is open source.",
            ),
            Evidence(
                field="is_open_source",
                value="true",
                source_url="https://official.example/",
                excerpt="The project is open source.",
            ),
            Evidence(
                field="pricing_model",
                value="Free",
                source_url="https://official.example/",
                excerpt="Invented quote not in the source",
            ),
        ],
    )
    workflow = Workflow.__new__(Workflow)
    workflow.llm = FakeLLM(structured_response=fake_analysis)
    workflow.prompts = DeveloperToolsPrompts()

    result = workflow._analyze_company_content(
        "Example", "https://official.example/", content
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].source_url == "https://official.example/"
    assert result.evidence[0].excerpt == content
