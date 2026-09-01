from __future__ import annotations

import html
from datetime import date

from ideo_digest.config import ResearchProfile
from ideo_digest.models import DigestItem, Paper, PaperAssessment


CATEGORY_LABELS = {
    "core_theory": "核心理论",
    "direct_hypothesis": "直接相关实证研究",
    "visual_or_behavioral_method": "视觉/行为实验方法",
    "online_method": "线上实验方法",
    "measurement": "测量与问卷",
    "adjacent": "邻近研究",
}

EVIDENCE_LABELS = {
    "empirical": "实证研究",
    "review": "综述",
    "methods": "方法文章",
    "preprint": "Preprint",
    "other": "其他",
}


def select_digest_items(
    papers: list[Paper],
    assessments: list[PaperAssessment],
    profile: ResearchProfile,
) -> list[DigestItem]:
    paper_map = {paper.candidate_id: paper for paper in papers}
    # A malformed or duplicated model item must never produce a repeated paper
    # in the email. Keep the highest-scored assessment for each known ID.
    best_by_id: dict[str, PaperAssessment] = {}
    for assessment in assessments:
        if assessment.candidate_id not in paper_map:
            continue
        current = best_by_id.get(assessment.candidate_id)
        if current is None or assessment.relevance_score > current.relevance_score:
            best_by_id[assessment.candidate_id] = assessment
    eligible = [
        assessment
        for assessment in best_by_id.values()
        if assessment.relevance_score >= profile.search.minimum_relevance_score
    ]
    eligible.sort(key=lambda item: item.relevance_score, reverse=True)
    return [
        DigestItem(paper=paper_map[item.candidate_id], assessment=item)
        for item in eligible[: profile.search.digest_max_items]
    ]


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _author_line(paper: Paper) -> str:
    if not paper.authors:
        return "Authors unavailable"
    if len(paper.authors) <= 5:
        return ", ".join(paper.authors)
    return ", ".join(paper.authors[:5]) + ", et al."


def render_html(
    items: list[DigestItem],
    profile: ResearchProfile,
    generated_on: date,
    date_window: tuple[date, date],
) -> str:
    start_date, end_date = date_window
    cards: list[str] = []
    for index, item in enumerate(items, start=1):
        paper = item.paper
        assessment = item.assessment
        category = CATEGORY_LABELS[assessment.category]
        evidence = EVIDENCE_LABELS[assessment.evidence_type]
        access_link = paper.open_access_url or paper.url
        access_label = "Open access / record" if paper.open_access_url else "DOI / record"
        cards.append(
            f"""
            <section class="paper-card">
              <div class="paper-number">{index}</div>
              <div class="score">相关性 {assessment.relevance_score}/100</div>
              <h2><a href="{_e(paper.url)}">{_e(paper.title)}</a></h2>
              <p class="meta">{_e(_author_line(paper))}<br>
                {_e(paper.publication_date.isoformat())} · {_e(paper.venue or 'Source unavailable')}
              </p>
              <p><span class="tag">{_e(category)}</span><span class="tag">{_e(evidence)}</span></p>
             <h3>研究内容 / Study Summary</h3>
              <p><strong>中文：</strong>{_e(assessment.study_summary_zh)}</p>
              <p lang="en"><strong>English:</strong> {_e(assessment.study_summary_en)}</p>

             <h3>为什么值得读 / Why It Matters</h3>
             <p><strong>中文：</strong>{_e(assessment.why_selected_zh)}</p>
             <p lang="en"><strong>English:</strong> {_e(assessment.why_selected_en)}</p>

             <h3>方法提示 / Methods Note</h3>
             <p><strong>中文：</strong>{_e(assessment.method_note_zh)}</p>
             <p lang="en"><strong>English:</strong> {_e(assessment.method_note_en)}</p>

             <h3>对 Phase 1 的应用 / Application to Phase 1</h3>
             <p><strong>中文：</strong>{_e(assessment.application_to_phase1_zh)}</p>
             <p lang="en"><strong>English:</strong> {_e(assessment.application_to_phase1_en)}</p>

             <h3>阅读时注意 / Cautions</h3>
             <p><strong>中文：</strong>{_e(assessment.caution_zh)}</p>
             <p lang="en"><strong>English:</strong> {_e(assessment.caution_en)}</p>

             <p class="link">
             <a href="{_e(access_link)}">查看原文 / Read Source →</a>
             </p>
            </section>
            """
        )

    item_count = len(items)
    cards_html = "\n".join(cards) if cards else "<p>本期没有达到相关性门槛的新论文。</p>"
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(profile.email.subject_prefix)}</title>
  <style>
    body {{ margin:0; background:#f4f1ea; color:#20211f; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif; line-height:1.65; }}
    .container {{ max-width:760px; margin:0 auto; padding:28px 18px 48px; }}
    .header {{ background:#173f3b; color:#f8f3e7; border-radius:18px; padding:30px; margin-bottom:22px; }}
    .header p {{ margin:8px 0 0; color:#dbe8df; }}
    h1 {{ margin:0; font-size:28px; line-height:1.25; }}
    h2 {{ font-size:21px; line-height:1.4; margin:10px 0 8px; }}
    h2 a {{ color:#173f3b; text-decoration:none; }}
    h3 {{ font-size:14px; text-transform:uppercase; letter-spacing:.04em; color:#536b62; margin:20px 0 3px; }}
    p {{ margin:5px 0 12px; }}
    .paper-card {{ position:relative; background:#fff; border:1px solid #ddd8cc; border-radius:16px; padding:25px 26px; margin:18px 0; box-shadow:0 4px 14px rgba(34,39,35,.05); }}
    .paper-number {{ width:32px; height:32px; display:inline-flex; align-items:center; justify-content:center; border-radius:50%; background:#dce8df; color:#173f3b; font-weight:700; }}
    .score {{ float:right; color:#8b4b2d; font-weight:700; font-size:14px; }}
    .meta {{ color:#68706a; font-size:14px; }}
    .tag {{ display:inline-block; background:#efe9dd; color:#4b524d; border-radius:999px; padding:3px 9px; margin:0 6px 4px 0; font-size:12px; }}
    .link a {{ color:#8b4b2d; font-weight:700; text-decoration:none; }}
    .footer {{ color:#71756f; font-size:12px; padding:16px 4px; }}
    @media (max-width:520px) {{ .paper-card,.header {{ padding:21px; }} h1 {{ font-size:24px; }} .score {{ float:none; margin-top:10px; }} }}
  </style>
</head>
<body>
  <main class="container">
    <header class="header">
      <h1>{_e(profile.email.subject_prefix)}</h1>
      <p>{_e(generated_on.isoformat())} · 本期精选 {item_count} 篇</p>
      <p>检索窗口：{_e(start_date.isoformat())} 至 {_e(end_date.isoformat())}</p>
    </header>
    {cards_html}
    <footer class="footer">
      本简报由公开学术元数据与摘要生成。AI 摘要不能替代阅读全文；正式研究决策前请核对原文、supplement 和 preregistration。
    </footer>
  </main>
</body>
</html>"""


def render_text(
    items: list[DigestItem],
    profile: ResearchProfile,
    generated_on: date,
    date_window: tuple[date, date],
) -> str:
    start_date, end_date = date_window
    lines = [
        profile.email.subject_prefix,
        f"生成日期：{generated_on.isoformat()}",
        f"检索窗口：{start_date.isoformat()} 至 {end_date.isoformat()}",
        "",
    ]
    if not items:
        lines.append("本期没有达到相关性门槛的新论文。")
        return "\n".join(lines)

    for index, item in enumerate(items, start=1):
        paper = item.paper
        assessment = item.assessment
        lines.extend(
            [
                f"{index}. {paper.title}",
                f"作者：{_author_line(paper)}",
                f"日期/来源：{paper.publication_date.isoformat()} · {paper.venue or 'Unknown'}",
                f"相关性：{assessment.relevance_score}/100 · {CATEGORY_LABELS[assessment.category]}",
                f"研究内容：{assessment.study_summary_zh}",
                f"Study Summary: {assessment.study_summary_en}",
                "",
                f"为什么值得读：{assessment.why_selected_zh}",
                f"Why It Matters: {assessment.why_selected_en}",
                "",
                f"方法提示：{assessment.method_note_zh}",
                f"Methods Note: {assessment.method_note_en}",
                "",
                f"对 Phase 1 的应用：{assessment.application_to_phase1_zh}",
                f"Application to Phase 1: {assessment.application_to_phase1_en}",
                "",
                f"阅读时注意：{assessment.caution_zh}",
                f"Cautions: {assessment.caution_en}",
                f"文章来源 / Read Source: {paper.open_access_url or paper.url}",
                "",
            ]
        )
    lines.append("AI 摘要不能替代阅读全文；正式研究决策前请核对原文。")
    return "\n".join(lines)
