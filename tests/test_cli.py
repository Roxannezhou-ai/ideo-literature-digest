from argparse import Namespace
from datetime import date

from ideo_digest.cli import run
from ideo_digest.models import Paper, PaperAssessment


def test_dry_run_pipeline_uses_mocks_and_writes_preview(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    paper = Paper(
        candidate_id="candidate-one",
        openalex_id="https://openalex.org/W1",
        doi="https://doi.org/10.1234/test",
        title="Prediction feedback and choice ownership",
        abstract="A behavioral experiment studies feedback and agency.",
        authors=["A. Researcher"],
        publication_date=date(2026, 8, 20),
        venue="Journal of Agency",
        url="https://doi.org/10.1234/test",
        open_access_url=None,
        work_type="article",
        cited_by_count=0,
        query_hits=["sense of agency"],
        best_search_rank=1,
    )

    def fake_fetch(self, start_date, end_date):
        return [paper]

    class FakeAssessor:
        def __init__(self, api_key, model):
            self.api_key = api_key
            self.model = model

        def assess(self, papers, profile):
            return [
                PaperAssessment(
                    candidate_id="candidate-one",
                    relevance_score=92,
                    category="direct_hypothesis",
                    evidence_type="empirical",
                    study_summary_zh="研究检验预测反馈与选择所有感。",
                    study_summary_en="The study examines prediction feedback and perceived ownership of choice.",

                    why_selected_zh="直接对应 Phase 1 操纵。",
                    why_selected_en="It directly corresponds to the Phase 1 manipulation.",

                    method_note_zh="行为实验。",
                    method_note_en="The paper reports a behavioral experiment.",

                   application_to_phase1_zh="可用于完善 post-survey。",
                   application_to_phase1_en="It may inform improvements to the post-experiment survey.",

                   caution_zh="需要阅读全文。",
                   caution_en="The full paper should be reviewed before drawing conclusions.",
                )
            ]

    monkeypatch.setattr("ideo_digest.cli.OpenAlexSource.fetch", fake_fetch)
    monkeypatch.setattr("ideo_digest.cli.LiteratureAssessor", FakeAssessor)

    output_dir = tmp_path / "output"
    state_path = tmp_path / "seen.json"
    args = Namespace(
        config="config/research_profile.yml",
        state=str(state_path),
        output_dir=str(output_dir),
        lookback_days=14,
        dry_run=True,
        include_seen=False,
    )
    assert run(args) == 0
    html_files = list(output_dir.glob("*.html"))
    text_files = list(output_dir.glob("*.txt"))
    assert len(html_files) == 1
    assert len(text_files) == 1
    assert "Prediction feedback and choice ownership" in html_files[0].read_text(
        encoding="utf-8"
    )
    assert not state_path.exists()
