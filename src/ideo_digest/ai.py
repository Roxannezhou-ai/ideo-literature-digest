from __future__ import annotations

import json

from openai import OpenAI

from ideo_digest.config import ResearchProfile
from ideo_digest.models import AssessmentBatch, Paper, PaperAssessment


SYSTEM_INSTRUCTIONS = """
You are a rigorous research literature screener for a visual cognition and
experimental psychology lab. Evaluate only the evidence in the supplied title,
metadata, and abstract. Do not invent sample sizes, methods, findings, or
implications that are not supported by that evidence. If the abstract is
missing or ambiguous, explicitly say so in the caution field and score
conservatively.

Direct relevance to the supplied Phase 1 paradigm matters more than generic
keyword overlap. Give the highest scores to work that can inform the study's
theory, prediction-feedback manipulation, agency/ownership measures,
confidence moderator, deception check, online speeded-response validity, or
post-experiment measurement. Write all explanatory fields in concise,
professional Chinese, while preserving established English technical terms
when useful.

Return exactly one assessment for every supplied candidate_id. A score of 65
means useful enough for the weekly digest; 80+ means directly actionable or
theoretically central. Treat preprints as preprints and identify uncertainty.
""".strip()


class LiteratureAssessor:
    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def assess(
        self,
        papers: list[Paper],
        profile: ResearchProfile,
    ) -> list[PaperAssessment]:
        payload = {
            "project_name": profile.project_name,
            "experiment_overview": profile.experiment_overview,
            "working_relevance_questions": profile.working_relevance_questions,
            "priority_topics": profile.priority_topics,
            "candidates": [paper.ai_payload() for paper in papers],
        }
        response = self.client.responses.parse(
            model=self.model,
            store=False,
            input=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False),
                },
            ],
            text_format=AssessmentBatch,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("OpenAI returned no parsed assessment")

        known_ids = {paper.candidate_id for paper in papers}
        assessments = [
            item for item in parsed.assessments if item.candidate_id in known_ids
        ]
        if not assessments:
            raise RuntimeError("OpenAI assessment did not contain any known candidate IDs")
        return assessments
