"""Run the reviewer panel and persist results.

Dispatches the document bundle to every reviewer concurrently (each on its own model),
collects structured :class:`Review` objects, and writes a per-run directory plus a human
digest. A failing reviewer (missing key, API error, unparseable output) is captured as an
errored Review rather than sinking the whole run.
"""
from __future__ import annotations

import datetime as _dt
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import context as ctxmod
from .personas import ReviewerSpec, load_panel
from .providers import ProviderError, get_provider
from .schema import REVIEW_JSON_SCHEMA, Review, parse_review

REPO = Path(__file__).resolve().parents[3]
DEFAULT_OUT = REPO / "results" / "reviews"

_USER_TEMPLATE = (
    "Here are the project documents to review.\n\n{context}\n\n"
    "----- TASK -----\n"
    "Produce your review as a single JSON object conforming to this JSON Schema "
    "(return JSON only, no surrounding prose):\n\n{schema}"
)


def _run_one(spec: ReviewerSpec, user: str, *, provider_override: str | None = None) -> Review:
    provider_name = provider_override or spec.provider
    try:
        provider = get_provider(provider_name)
        raw = provider.generate(
            spec.system_prompt, user, model=spec.model,
            max_tokens=spec.max_tokens, temperature=spec.temperature, json_mode=True)
    except ProviderError as e:
        return Review(spec.id, spec.name, provider_name, spec.model,
                      payload={}, error=str(e))
    return parse_review(spec.id, spec.name, provider_name, spec.model, raw)


def run_panel(docs: list[str] | None = None, *, config_path: Path | None = None,
              out_dir: Path = DEFAULT_OUT, dry_run: bool = False,
              max_workers: int = 3) -> dict:
    """Run all reviewers and write the results. Returns the run record dict."""
    specs = load_panel(config_path=config_path)
    context = ctxmod.build_context(docs)
    user = _USER_TEMPLATE.format(context=context,
                                 schema=json.dumps(REVIEW_JSON_SCHEMA, indent=2))
    override = "mock" if dry_run else None

    reviews: list[Review] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {pool.submit(_run_one, s, user, provider_override=override): s for s in specs}
        for fut in as_completed(futs):
            reviews.append(fut.result())
    reviews.sort(key=lambda r: r.reviewer_id)

    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_dir / stamp
    run_dir.mkdir(parents=True, exist_ok=True)
    for r in reviews:
        (run_dir / f"{r.reviewer_id}.json").write_text(
            json.dumps(r.to_dict(), ensure_ascii=False, indent=2))

    record = {
        "timestamp": stamp,
        "dry_run": dry_run,
        "documents": ctxmod.manifest(docs),
        "reviewers": [{"id": r.reviewer_id, "name": r.reviewer_name,
                       "provider": r.provider, "model": r.model,
                       "ok": r.ok, "error": r.error} for r in reviews],
    }
    (run_dir / "run.json").write_text(json.dumps(record, indent=2))
    digest = build_digest(reviews, record)
    (run_dir / "digest.md").write_text(digest)
    record["run_dir"] = str(run_dir)
    record["digest"] = digest
    return record


def build_digest(reviews: list[Review], record: dict) -> str:
    """Human-readable cross-reviewer summary written alongside the JSON."""
    lines = [f"# Reviewer panel digest — {record['timestamp']}", ""]
    if record["dry_run"]:
        lines.append("> DRY RUN (mock provider; no API calls).\n")
    for r in reviews:
        lines.append(f"## {r.reviewer_name}  ·  {r.provider}/{r.model}")
        if not r.ok:
            lines.append(f"**FAILED:** {r.error}\n")
            continue
        p = r.payload
        lines.append(f"**Recommendation:** {p.get('recommendation', '?')}  ")
        sc = p.get("scores", {})
        if sc:
            lines.append("**Scores:** " + ", ".join(f"{k} {v}" for k, v in sc.items()))
        lines.append(f"\n{p.get('summary', '').strip()}\n")
        majors = p.get("major_concerns", [])
        if majors:
            lines.append("**Major concerns:**")
            for m in majors:
                lines.append(f"- *({m.get('severity','?')})* {m.get('issue','')} "
                             f"— {m.get('evidence_location','')}")
        ai = p.get("ai_authorship", {})
        if ai:
            lines.append(f"\n**AI-authorship:** likelihood {ai.get('overall_likelihood')} "
                         f"(confidence {ai.get('confidence')}), {len(ai.get('tells', []))} tells")
        lines.append("")
    return "\n".join(lines)
