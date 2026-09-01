from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


@dataclass(slots=True)
class Paper:
    candidate_id: str
    openalex_id: str
    doi: str | None
    title: str
    abstract: str
    authors: list[str]
    publication_date: date
    venue: str | None
    url: str
    open_access_url: str | None
    work_type: str
    cited_by_count: int
    query_hits: list[str] = field(default_factory=list)
    best_search_rank: int = 999
    heuristic_score: float = 0.0

    def ai_payload(self, abstract_limit: int = 3_000) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "title": self.title,
            "authors": self.authors[:8],
            "publication_date": self.publication_date.isoformat(),
            "venue": self.venue or "Unknown",
            "work_type": self.work_type,
            "abstract": self.abstract[:abstract_limit] or "Abstract unavailable.",
            "search_query_hits": self.query_hits,
            "heuristic_score": round(self.heuristic_score, 1),
            "url": self.url,
        }


class PaperAssessment(BaseModel):
    candidate_id: str
    relevance_score: int = Field(ge=0, le=100)
    category: Literal[
        "core_theory",
        "direct_hypothesis",
        "visual_or_behavioral_method",
        "online_method",
        "measurement",
        "adjacent",
    ]
    evidence_type: Literal["empirical", "review", "methods", "preprint", "other"]
    study_summary_zh: str
study_summary_en: str
why_selected_zh: str
why_selected_en: str
method_note_zh: str
method_note_en: str
application_to_phase1_zh: str
application_to_phase1_en: str
caution_zh: str
caution_en: str


class AssessmentBatch(BaseModel):
    assessments: list[PaperAssessment]


@dataclass(slots=True)
class DigestItem:
    paper: Paper
    assessment: PaperAssessment

