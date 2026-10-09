"""Validated data models for source-aware technical research."""
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class Evidence(BaseModel):
    """A traceable excerpt supporting a single research claim."""
    model_config = ConfigDict(extra="forbid")

    field: str
    value: str
    source_url: str
    excerpt: str = ""
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CompanyAnalysis(BaseModel):
    """Structured extraction; null/empty means the source did not establish a fact."""
    model_config = ConfigDict(extra="forbid")

    pricing_model: str = "Unknown"
    is_open_source: bool | None = None
    tech_stack: list[str] = Field(default_factory=list)
    description: str = ""
    api_available: bool | None = None
    language_support: list[str] = Field(default_factory=list)
    integration_capabilities: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class CompanyInfo(BaseModel):
    name: str
    description: str = ""
    website: str = ""
    pricing_model: str | None = "Unknown"
    is_open_source: bool | None = None
    tech_stack: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    api_available: bool | None = None
    language_support: list[str] = Field(default_factory=list)
    integration_capabilities: list[str] = Field(default_factory=list)
    developer_experience_rating: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    research_status: str = "completed"


class ResearchState(BaseModel):
    query: str
    extracted_tools: list[str] = Field(default_factory=list)
    companies: list[CompanyInfo] = Field(default_factory=list)
    search_results: list[dict[str, Any]] = Field(default_factory=list)
    analysis: str | None = None
    errors: list[str] = Field(default_factory=list)
