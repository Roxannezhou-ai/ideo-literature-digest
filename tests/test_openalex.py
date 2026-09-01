from datetime import date

from ideo_digest.openalex import (
    merge_duplicates,
    paper_identity,
    parse_work,
    reconstruct_abstract,
)


def sample_work() -> dict:
    return {
        "id": "https://openalex.org/W123",
        "doi": "https://doi.org/10.1234/example",
        "display_name": "Prediction Feedback and the Sense of Agency",
        "publication_date": "2026-08-20",
        "authorships": [
            {"author": {"display_name": "A. Researcher"}},
            {"author": {"display_name": "B. Scientist"}},
        ],
        "primary_location": {
            "landing_page_url": "https://journal.example/paper",
            "source": {"display_name": "Journal of Agency"},
        },
        "best_oa_location": {"pdf_url": "https://example.org/paper.pdf"},
        "abstract_inverted_index": {
            "Agency": [4],
            "Prediction": [0],
            "feedback": [1],
            "changes": [2],
            "perceived": [3],
        },
        "cited_by_count": 2,
        "type": "article",
    }


def test_reconstruct_abstract_orders_words() -> None:
    assert reconstruct_abstract({"world": [1], "Hello": [0]}) == "Hello world"
    assert reconstruct_abstract(None) == ""


def test_parse_work_extracts_core_fields() -> None:
    paper = parse_work(sample_work(), query="sense of agency", rank=3)
    assert paper is not None
    assert paper.publication_date == date(2026, 8, 20)
    assert paper.venue == "Journal of Agency"
    assert paper.abstract == "Prediction feedback changes perceived Agency"
    assert paper.open_access_url == "https://example.org/paper.pdf"
    assert paper.query_hits == ["sense of agency"]


def test_merge_duplicates_combines_query_evidence() -> None:
    first = parse_work(sample_work(), query="sense of agency", rank=5)
    second = parse_work(sample_work(), query="prediction feedback", rank=2)
    assert first is not None and second is not None
    merged = merge_duplicates([first, second])
    assert len(merged) == 1
    assert set(merged[0].query_hits) == {"sense of agency", "prediction feedback"}
    assert merged[0].best_search_rank == 2


def test_paper_identity_prefers_doi() -> None:
    assert paper_identity("https://doi.org/10.1/a", "Title A") == paper_identity(
        "https://doi.org/10.1/a", "Completely different title"
    )

