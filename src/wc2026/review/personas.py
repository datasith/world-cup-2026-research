"""Load the reviewer panel config and persona prompts (prompt-as-data).

Resolves each reviewer's persona markdown and shared rubric from ``reviewers/``, and lets
model ids be overridden per provider via REVIEW_<PROVIDER>_MODEL env vars so the latest
model can be selected without editing config.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REVIEWERS_DIR = REPO / "reviewers"


@dataclass
class ReviewerSpec:
    id: str
    name: str
    provider: str
    model: str
    system_prompt: str            # rubric + persona, assembled
    max_tokens: int
    temperature: float


def _resolve_model(provider: str, configured: str) -> str:
    """Env override REVIEW_<PROVIDER>_MODEL wins over the config value."""
    return os.environ.get(f"REVIEW_{provider.upper()}_MODEL", configured)


def load_panel(config_path: Path | None = None,
               reviewers_dir: Path = REVIEWERS_DIR) -> list[ReviewerSpec]:
    config_path = config_path or (reviewers_dir / "config.json")
    cfg = json.loads(config_path.read_text())
    defaults = cfg.get("defaults", {})
    rubric = (reviewers_dir / "rubric.md").read_text()

    specs: list[ReviewerSpec] = []
    for r in cfg["reviewers"]:
        persona = (reviewers_dir / r["persona"]).read_text()
        system = (f"{rubric}\n\n----- YOUR PERSONA -----\n{persona}\n\n"
                  "Review the documents that follow. Return ONLY the JSON object.")
        model = _resolve_model(r["provider"], r["model"])
        specs.append(ReviewerSpec(
            id=r["id"], name=r["name"], provider=r["provider"], model=model,
            system_prompt=system,
            max_tokens=r.get("max_tokens", defaults.get("max_tokens", 4096)),
            temperature=r.get("temperature", defaults.get("temperature", 0.2)),
        ))
    return specs
