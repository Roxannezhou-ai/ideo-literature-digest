from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from ideo_digest.ai import LiteratureAssessor
from ideo_digest.config import RuntimeSettings, load_profile
from ideo_digest.digest import render_html, render_text, select_digest_items
from ideo_digest.emailer import send_gmail
from ideo_digest.openalex import OpenAlexSource
from ideo_digest.ranking import rank_candidates
from ideo_digest.state import SeenState


LOGGER = logging.getLogger("ideo_digest")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find, assess, and email a weekly IDEO academic literature digest."
    )
    parser.add_argument(
        "--config",
        default="config/research_profile.yml",
        help="Path to the research profile YAML.",
    )
    parser.add_argument(
        "--state",
        default="data/seen.json",
        help="Path to the persistent seen-paper state.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for generated HTML and text previews.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Override the configured publication lookback window.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate files without sending email or updating seen state.",
    )
    parser.add_argument(
        "--include-seen",
        action="store_true",
        help="Include papers already present in seen state (useful for testing).",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    profile = load_profile(args.config)
    settings = RuntimeSettings.from_environment(require_email=not args.dry_run)
    timezone = ZoneInfo(profile.timezone)
    now = datetime.now(timezone)
    end_date = now.date()
    lookback_days = args.lookback_days or profile.search.lookback_days
    if lookback_days < 1:
        raise ValueError("lookback-days must be at least 1")
    start_date = end_date - timedelta(days=lookback_days)

    state = SeenState(args.state)
    source = OpenAlexSource(
        profile=profile,
        api_key=settings.openalex_api_key,
        contact_email=settings.email_address or None,
    )
    LOGGER.info("Searching OpenAlex from %s to %s", start_date, end_date)
    papers = source.fetch(start_date=start_date, end_date=end_date)
    LOGGER.info("Retrieved %d unique candidate papers", len(papers))

    if not args.include_seen:
        papers = [paper for paper in papers if paper.candidate_id not in state.ids]
    LOGGER.info("%d candidates remain after seen-paper filtering", len(papers))

    ranked = rank_candidates(papers, profile)
    ai_candidates = ranked[: profile.search.candidate_limit]
    items = []
    if ai_candidates:
        assessor = LiteratureAssessor(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
        assessments = assessor.assess(ai_candidates, profile)
        items = select_digest_items(ai_candidates, assessments, profile)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    date_window = (start_date, end_date)
    html_body = render_html(items, profile, end_date, date_window)
    text_body = render_text(items, profile, end_date, date_window)
    output_stem = output_dir / f"ideo-digest-{end_date.isoformat()}"
    output_stem.with_suffix(".html").write_text(html_body, encoding="utf-8")
    output_stem.with_suffix(".txt").write_text(text_body, encoding="utf-8")
    LOGGER.info("Generated digest preview with %d paper(s)", len(items))

    if args.dry_run:
        LOGGER.info("Dry run complete; no email sent and seen state unchanged")
        return 0

    if not items and not profile.email.send_when_empty:
        LOGGER.info("No qualifying new papers; email skipped")
        return 0

    subject = f"{profile.email.subject_prefix}｜{end_date.isoformat()}｜{len(items)}篇"
    send_gmail(
        sender=settings.email_address,
        recipient=settings.email_to,
        app_password=settings.gmail_app_password,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
    LOGGER.info("Digest sent to %s", settings.email_to)

    if items:
        state.mark_sent(items, sent_at=now)
        state.save()
        LOGGER.info("Seen-paper state updated")
    return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    parser = build_parser()
    args = parser.parse_args()
    try:
        raise SystemExit(run(args))
    except Exception:
        LOGGER.exception("Digest generation failed")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

