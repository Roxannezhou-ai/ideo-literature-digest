from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


class SearchConfig(BaseModel):
    lookback_days: int = Field(default=14, ge=1, le=3650)
    results_per_query: int = Field(default=25, ge=1, le=100)
    candidate_limit: int = Field(default=18, ge=1, le=50)
    minimum_relevance_score: int = Field(default=65, ge=0, le=100)
    digest_min_items: int = Field(default=3, ge=1, le=20)
    digest_max_items: int = Field(default=5, ge=1, le=20)
    include_work_types: list[str] = Field(default_factory=lambda: ["article", "preprint"])

    @model_validator(mode="after")
    def validate_limits(self) -> "SearchConfig":
        if self.digest_min_items > self.digest_max_items:
            raise ValueError("digest_min_items cannot exceed digest_max_items")
        if self.digest_max_items > self.candidate_limit:
            raise ValueError("digest_max_items cannot exceed candidate_limit")
        return self


class EmailConfig(BaseModel):
    subject_prefix: str = "IDEO 每周研究简报"
    send_when_empty: bool = False


class ResearchProfile(BaseModel):
    project_name: str
    timezone: str = "America/Vancouver"
    experiment_overview: str
    working_relevance_questions: list[str]
    priority_topics: list[str]
    search_queries: list[str] = Field(min_length=1)
    priority_terms: list[str]
    exclude_terms: list[str] = Field(default_factory=list)
    search: SearchConfig = Field(default_factory=SearchConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)


@dataclass(frozen=True, slots=True)
class RuntimeSettings:
    openai_api_key: str
    openai_model: str
    email_address: str
    gmail_app_password: str
    email_to: str
    openalex_api_key: str | None

    @classmethod
    def from_environment(cls, require_email: bool = True) -> "RuntimeSettings":
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        email_address = os.getenv("EMAIL_ADDRESS", "").strip()
        gmail_password = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
        email_to = os.getenv("EMAIL_TO", "").strip() or email_address

        missing: list[str] = []
        if not openai_api_key:
            missing.append("OPENAI_API_KEY")
        if require_email and not email_address:
            missing.append("EMAIL_ADDRESS")
        if require_email and not gmail_password:
            missing.append("GMAIL_APP_PASSWORD")
        if missing:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing)
            )

        return cls(
            openai_api_key=openai_api_key,
            openai_model=os.getenv("OPENAI_MODEL", "").strip() or "gpt-5.6-terra",
            email_address=email_address,
            gmail_app_password=gmail_password,
            email_to=email_to,
            openalex_api_key=os.getenv("OPENALEX_API_KEY", "").strip() or None,
        )


def load_profile(path: str | Path) -> ResearchProfile:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Research profile not found: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Research profile must contain a YAML mapping")
    return ResearchProfile.model_validate(raw)

