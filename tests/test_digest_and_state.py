from datetime import date, datetime, timezone

from ideo_digest.config import load_profile
from ideo_digest.digest import render_html, select_digest_items
from ideo_digest.models import Paper, PaperAssessment
from ideo_digest.state import SeenState


def make_paper(candidate_id: str, title: str = "Agency <Study>") -> Paper:
    return Paper(
        candidate_id=candidate_id,
        openalex_id=f"W{candidate_id}",
        doi=None,
        title=title,
        abstract="Abstract",
        authors=["A. Author"],
        publication_date=date(2026, 8, 20),
        venue="A Journal",
        url=f"https://example.org/{candidate_id}?a=1&b=2",
        open_access_url=None,
        work_type="article",
        cited_by_count=0,
    )


def make_assessment(candidate_id: str, score: int) -> PaperAssessment:
    return PaperAssessment(
        candidate_id=candidate_id,
        relevance_score=score,
        category="direct_hypothesis",
        evidence_type="empirical",

        study_summary_zh="摘要",
        study_summary_en="The study examines prediction feedback and perceived ownership of choice.",

        why_selected_zh="相关",
        why_selected_en="It directly corresponds to the Phase 1 manipulation.",

        method_note_zh="方法",
        method_note_en="The paper reports a behavioral experiment.",

        application_to_phase1_zh="应用",
        application_to_phase1_en="It may inform improvements to the post-experiment survey.",

        caution_zh="限制",
        caution_en="The full paper should be reviewed before drawing conclusions.",
    )


def test_selection_applies_threshold_and_order() -> None:
    profile = load_profile("config/research_profile.yml")
    papers = [make_paper("one"), make_paper("two"), make_paper("three")]
    assessments = [
        make_assessment("one", 70),
        make_assessment("two", 90),
        make_assessment("three", 50),
    ]
    selected = select_digest_items(papers, assessments, profile)
    assert [item.paper.candidate_id for item in selected] == ["two", "one"]


def test_selection_deduplicates_model_assessments() -> None:
    profile = load_profile("config/research_profile.yml")
    paper = make_paper("one")
    selected = select_digest_items(
        [paper],
        [make_assessment("one", 70), make_assessment("one", 90)],
        profile,
    )
    assert len(selected) == 1
    assert selected[0].assessment.relevance_score == 90


def test_html_escapes_metadata() -> None:
    profile = load_profile("config/research_profile.yml")
    paper = make_paper("one")
    item = select_digest_items([paper], [make_assessment("one", 90)], profile)[0]
    rendered = render_html(
        [item], profile, date(2026, 9, 1), (date(2026, 8, 18), date(2026, 9, 1))
    )
    assert "Agency &lt;Study&gt;" in rendered
    assert "&amp;b=2" in rendered
    assert "<Study>" not in rendered


def test_seen_state_round_trip(tmp_path) -> None:
    path = tmp_path / "seen.json"
    state = SeenState(path)
    profile = load_profile("config/research_profile.yml")
    paper = make_paper("one")
    item = select_digest_items([paper], [make_assessment("one", 90)], profile)[0]
    state.mark_sent([item], datetime(2026, 9, 1, tzinfo=timezone.utc))
    state.save()
    reloaded = SeenState(path)
    assert reloaded.ids == {"one"}
