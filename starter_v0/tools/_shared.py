from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 20


def err(tool: str, exc: Exception) -> dict[str, str]:
    return {"error": type(exc).__name__, "tool": tool, "message": str(exc)}


def domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().removeprefix("www.")


def fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def terms(query: str) -> set[str]:
    return {term for term in re.findall(r"[a-z0-9]+", fold_text(query)) if len(term) > 1}
