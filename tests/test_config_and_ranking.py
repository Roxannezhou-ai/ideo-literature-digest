from datetime import date

import pytest
from pydantic import ValidationError

from ideo_digest.config import ResearchProfile, load_profile
from ideo_digest.models import Paper
from ideo_digest.ranking import heuristic_score


def test_repository_profile_loads() -> None:
    profile = load_profile("config/research_profile.yml")
    assert profile.timezone == "America/Vancouver"
    assert profile.search.digest_max_items == 5
    assert any("sense of agency" in query for query in profile.search_queries)


def test_invalid_digest_limits_are_rejected() -> None:
    base = {
        "project_name": "test",
        "experiment_overview": "test",
        "working_relevance_questions": ["q"],
        "priority_topics": ["t"],
        "search_queries": ["q"],
        "priority_terms": ["agency"],
        "search": {
            "candidate_limit": 2,
            "digest_min_items": 3,
            "digest_max_items": 5,
        },
    }
    with pytest.raises(ValidationError):
        ResearchProfile.model_validate(base)


def test_directly_relevant_paper_scores_above_irrelevant_one() -> None:
    profile = load_profile("config/research_profile.yml")
    relevant = Paper(
        candidate_id="1",
        openalex_id="W1",
        doi=None,
        title="Prediction feedback changes the sense of agency",
        abstract="An online experiment tests ideomotor action-effect learning.",
        authors=[],
        publication_date=date.today(),
        venue=None,
        url="https://example.org/1",
        open_access_url=None,
        work_type="article",
        cited_by_count=0,
        query_hits=["sense of agency", "prediction feedback"],
        best_search_rank=1,
    )
    irrelevant = Paper(
        candidate_id="2",
        openalex_id="W2",
        doi=None,
        title="Efficient industrial motor vehicle control",
        abstract="A robot actuator engineering study.",
        authors=[],
        publication_date=date.today(),
        venue=None,
        url="https://example.org/2",
        open_access_url=None,
        work_type="article",
        cited_by_count=0,
        query_hits=["motor"],
        best_search_rank=10,
    )
    assert heuristic_score(relevant, profile) > heuristic_score(irrelevant, profile)

