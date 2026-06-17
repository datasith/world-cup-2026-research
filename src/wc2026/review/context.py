"""Assemble the document bundle handed to each reviewer.

Gathers the manuscript and the supporting project documents into one delimited packet
so a reviewer sees the whole argument (theory, design, results, pre-registration, draft)
and can check claims for internal consistency across them.
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

# Order matters: lead with the manuscript, then the scaffolding that backs it.
DEFAULT_DOCS = [
    "paper/main.tex",
    "THEORY.md",
    "DESIGN.md",
    "RESULTS.md",
    "PREREGISTRATION.md",
]


def build_context(docs: list[str] | None = None, repo: Path = REPO,
                  max_chars_per_doc: int = 60_000) -> str:
    """Return a single delimited string of the requested documents.

    Missing files are noted rather than skipped silently, so a reviewer (and the audit
    log) can see exactly what was and wasn't provided.
    """
    docs = docs or DEFAULT_DOCS
    parts: list[str] = []
    for rel in docs:
        path = repo / rel
        header = f"===== BEGIN {rel} ====="
        footer = f"===== END {rel} ====="
        if not path.exists():
            parts.append(f"{header}\n[FILE NOT FOUND]\n{footer}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars_per_doc:
            text = text[:max_chars_per_doc] + f"\n[...truncated at {max_chars_per_doc} chars...]"
        parts.append(f"{header}\n{text}\n{footer}")
    return "\n\n".join(parts)


def manifest(docs: list[str] | None = None, repo: Path = REPO) -> list[dict]:
    """List the docs in the bundle with presence + size, for the run record."""
    docs = docs or DEFAULT_DOCS
    out = []
    for rel in docs:
        path = repo / rel
        out.append({"path": rel, "exists": path.exists(),
                    "chars": path.stat().st_size if path.exists() else 0})
    return out
