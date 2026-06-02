from __future__ import annotations

from pathlib import Path
from typing import Any

from tools._shared import ROOT, err, terms


NOTES_DIR = ROOT / "topic_notes"


def _sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    title = "Overview"
    lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if lines:
                sections.append((title, lines))
            title = line[3:].strip()
            lines = []
        elif line.startswith("# "):
            title = line[2:].strip()
        else:
            lines.append(line)
    if lines:
        sections.append((title, lines))
    return [(section_title, "\n".join(section_lines).strip()) for section_title, section_lines in sections if "\n".join(section_lines).strip()]


def search_topic_notes(query: str = "", top_k: int = 3) -> dict[str, Any]:
    try:
        query_terms = terms(query)
        limit = max(1, int(top_k or 3))

        hits: list[dict[str, Any]] = []
        fallback_hits: list[dict[str, Any]] = []
        for path in sorted(NOTES_DIR.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            doc_terms = terms(path.stem)
            for section, body in _sections(raw):
                excerpt = " ".join(line.strip() for line in body.splitlines() if line.strip())
                fallback_hits.append({
                    "doc_id": path.stem,
                    "section": section,
                    "excerpt": excerpt[:1000],
                    "score": 0,
                    "source": str(path.relative_to(ROOT)),
                })
                if not query_terms:
                    continue
                section_terms = terms(" ".join([section, body]))
                score = len(query_terms & section_terms) + 2 * len(query_terms & doc_terms)
                if score <= 0:
                    continue
                hits.append({
                    "doc_id": path.stem,
                    "section": section,
                    "excerpt": excerpt[:1000],
                    "score": score,
                    "source": str(path.relative_to(ROOT)),
                })

        hits.sort(key=lambda item: item["score"], reverse=True)
        results = hits[:limit] if hits else fallback_hits[:limit]
        return {
            "tool": "search_topic_notes",
            "query": query,
            "results": results,
            "freshness": "static_demo_focus_notes",
        }
    except Exception as exc:
        return err("search_topic_notes", exc)
