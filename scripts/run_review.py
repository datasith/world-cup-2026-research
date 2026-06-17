"""Run the 3-model LLM-as-judge reviewer panel over the manuscript + project docs.

Each reviewer (Theorist/Anthropic, Domain Skeptic/OpenAI, Methodologist/Google) returns a
structured critique incl. an AI-authorship assessment. Results land in
``results/reviews/<timestamp>/`` (per-reviewer JSON + run.json + digest.md).

Keys (env): ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY.
Model ids: from reviewers/config.json, overridable via REVIEW_<PROVIDER>_MODEL.

Usage:
  uv run python scripts/run_review.py                 # live run (needs keys)
  uv run python scripts/run_review.py --dry-run       # offline mock, no keys needed
  uv run python scripts/run_review.py --docs paper/main.tex THEORY.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wc2026.review.orchestrator import run_panel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", nargs="*", default=None,
                    help="doc paths (relative to repo root); default = the standard bundle")
    ap.add_argument("--dry-run", action="store_true",
                    help="use the offline mock provider (no API keys/calls)")
    ap.add_argument("--config", type=str, default=None, help="path to reviewers/config.json")
    args = ap.parse_args()

    record = run_panel(docs=args.docs,
                       config_path=Path(args.config) if args.config else None,
                       dry_run=args.dry_run)

    print(f"\n=== reviewer panel {'(DRY RUN) ' if args.dry_run else ''}===")
    for r in record["reviewers"]:
        status = "ok" if r["ok"] else f"FAILED ({r['error']})"
        print(f"  {r['name']:<22} {r['provider']}/{r['model']:<20} {status}")
    print(f"\nresults -> {record['run_dir']}")
    print(f"digest  -> {record['run_dir']}/digest.md")


if __name__ == "__main__":
    main()
