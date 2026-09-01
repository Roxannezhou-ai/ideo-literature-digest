from __future__ import annotations

import math
import re

from ideo_digest.config import ResearchProfile
from ideo_digest.models import Paper


def _contains_term(text: str, term: str) -> bool:
    normalized_term = term.casefold().strip()
    if not normalized_term:
        return False
    if " " in normalized_term or "-" in normalized_term:
        return normalized_term in text
    return re.search(rf"\b{re.escape(normalized_term)}\b", text) is not None


def heuristic_score(paper: Paper, profile: ResearchProfile) -> float:
    title = paper.title.casefold()
    body = f"{paper.title} {paper.abstract}".casefold()

    score = 0.0
    for term in profile.priority_terms:
        if _contains_term(title, term):
            score += 7.0
        elif _contains_term(body, term):
            score += 3.5

    score += min(len(paper.query_hits), 5) * 4.0
    score += max(0.0, 8.0 - math.log2(max(paper.best_search_rank, 1) + 1) * 2.0)
    score += min(math.log2(paper.cited_by_count + 1), 4.0)

    if paper.abstract:
        score += 4.0
    else:
        score -= 8.0
    if paper.open_access_url:
        score += 1.5

    for term in profile.exclude_terms:
        if term.casefold() in body:
            score -= 20.0

    return round(score, 2)


def rank_candidates(papers: list[Paper], profile: ResearchProfile) -> list[Paper]:
    for paper in papers:
        paper.heuristic_score = heuristic_score(paper, profile)
    return sorted(
        papers,
        key=lambda paper: (
            paper.heuristic_score,
            len(paper.query_hits),
            paper.publication_date,
        ),
        reverse=True,
    )

