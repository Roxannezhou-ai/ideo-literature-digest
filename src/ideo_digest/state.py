from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ideo_digest.models import DigestItem


class SeenState:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.records: list[dict[str, str]] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        records = payload.get("seen", []) if isinstance(payload, dict) else []
        if isinstance(records, list):
            self.records = [item for item in records if isinstance(item, dict)]

    @property
    def ids(self) -> set[str]:
        return {str(item.get("id")) for item in self.records if item.get("id")}

    def mark_sent(self, items: list[DigestItem], sent_at: datetime) -> None:
        existing = self.ids
        for item in items:
            if item.paper.candidate_id in existing:
                continue
            self.records.append(
                {
                    "id": item.paper.candidate_id,
                    "title": item.paper.title,
                    "sent_at": sent_at.isoformat(),
                    "url": item.paper.url,
                }
            )
            existing.add(item.paper.candidate_id)
        self.records = self.records[-2000:]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": 1, "seen": self.records}
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

