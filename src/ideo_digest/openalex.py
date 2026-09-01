from __future__ import annotations

import hashlib
import re
from datetime import date
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ideo_digest.config import ResearchProfile
from ideo_digest.models import Paper


OPENALEX_WORKS_URL = "https://api.openalex.org/works"


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    positioned: list[tuple[int, str]] = []
    for word, positions in inverted_index.items():
        positioned.extend((position, word) for position in positions)
    positioned.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned)


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", title.casefold())


def paper_identity(doi: str | None, title: str) -> str:
    stable_value = (doi or normalize_title(title)).casefold().strip()
    return hashlib.sha256(stable_value.encode("utf-8")).hexdigest()[:20]


def _doi_url(doi: str | None) -> str | None:
    if not doi:
        return None
    return doi if doi.startswith("http") else f"https://doi.org/{doi}"


def _location_url(location: dict[str, Any] | None) -> str | None:
    if not location:
        return None
    return location.get("pdf_url") or location.get("landing_page_url")


def _venue_name(location: dict[str, Any] | None) -> str | None:
    if not location:
        return None
    source = location.get("source") or {}
    return source.get("display_name")


def _authors(authorships: list[dict[str, Any]] | None) -> list[str]:
    names: list[str] = []
    for authorship in authorships or []:
        name = (authorship.get("author") or {}).get("display_name")
        if name:
            names.append(name)
    return names


def parse_work(raw: dict[str, Any], query: str, rank: int) -> Paper | None:
    title = (raw.get("display_name") or raw.get("title") or "").strip()
    published = raw.get("publication_date")
    openalex_id = (raw.get("id") or "").strip()
    if not title or not published or not openalex_id:
        return None

    doi = _doi_url(raw.get("doi"))
    primary_location = raw.get("primary_location") or {}
    best_oa_location = raw.get("best_oa_location") or {}
    open_access_url = _location_url(best_oa_location)
    url = doi or open_access_url or _location_url(primary_location) or openalex_id

    return Paper(
        candidate_id=paper_identity(doi, title),
        openalex_id=openalex_id,
        doi=doi,
        title=title,
        abstract=reconstruct_abstract(raw.get("abstract_inverted_index")),
        authors=_authors(raw.get("authorships")),
        publication_date=date.fromisoformat(published),
        venue=_venue_name(primary_location) or _venue_name(best_oa_location),
        url=url,
        open_access_url=open_access_url,
        work_type=raw.get("type") or "unknown",
        cited_by_count=int(raw.get("cited_by_count") or 0),
        query_hits=[query],
        best_search_rank=rank,
    )


def merge_duplicates(papers: list[Paper]) -> list[Paper]:
    merged: dict[str, Paper] = {}
    for paper in papers:
        existing = merged.get(paper.candidate_id)
        if existing is None:
            merged[paper.candidate_id] = paper
            continue
        existing.best_search_rank = min(existing.best_search_rank, paper.best_search_rank)
        for query in paper.query_hits:
            if query not in existing.query_hits:
                existing.query_hits.append(query)
        if not existing.abstract and paper.abstract:
            existing.abstract = paper.abstract
        if not existing.open_access_url and paper.open_access_url:
            existing.open_access_url = paper.open_access_url
    return list(merged.values())


class OpenAlexSource:
    def __init__(
        self,
        profile: ResearchProfile,
        api_key: str | None = None,
        contact_email: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.profile = profile
        self.api_key = api_key
        self.contact_email = contact_email
        self.session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=4,
            backoff_factor=1.0,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        session.headers.update(
            {"User-Agent": "ideo-literature-digest/0.1 (academic literature monitoring)"}
        )
        return session

    def fetch(self, start_date: date, end_date: date) -> list[Paper]:
        all_papers: list[Paper] = []
        for query in self.profile.search_queries:
            all_papers.extend(self._fetch_query(query, start_date, end_date))
        return merge_duplicates(all_papers)

    def _fetch_query(self, query: str, start_date: date, end_date: date) -> list[Paper]:
        work_types = "|".join(self.profile.search.include_work_types)
        filters = [
            f"from_publication_date:{start_date.isoformat()}",
            f"to_publication_date:{end_date.isoformat()}",
        ]
        if work_types:
            filters.append(f"type:{work_types}")

        params: dict[str, str | int] = {
            "search": query,
            "filter": ",".join(filters),
            "per-page": self.profile.search.results_per_query,
            "select": (
                "id,doi,display_name,publication_date,authorships,primary_location,"
                "best_oa_location,abstract_inverted_index,cited_by_count,type"
            ),
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.contact_email:
            params["mailto"] = self.contact_email

        response = self.session.get(OPENALEX_WORKS_URL, params=params, timeout=(10, 45))
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results", [])
        papers: list[Paper] = []
        for rank, raw in enumerate(results, start=1):
            paper = parse_work(raw, query=query, rank=rank)
            if paper is not None:
                papers.append(paper)
        return papers

