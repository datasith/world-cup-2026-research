"""Tests for the reviewer subsystem -- no network, no API keys.

Exercises JSON extraction, schema normalization, persona/config loading, the mock
provider, and a full dry-run of the orchestrator.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.wc2026.review import context as ctxmod
from src.wc2026.review.env import load_dotenv
from src.wc2026.review.orchestrator import run_panel
from src.wc2026.review.personas import load_panel
from src.wc2026.review.providers import MockProvider, get_provider, ProviderError
from src.wc2026.review.schema import extract_json, parse_review


def test_extract_json_plain():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_wrapped_in_prose_and_fences():
    raw = 'Sure!\n```json\n{"a": {"b": 2}, "c": "}"}\n```\nhope that helps'
    assert extract_json(raw) == {"a": {"b": 2}, "c": "}"}


def test_extract_json_raises_on_garbage():
    with pytest.raises(ValueError):
        extract_json("no json here at all")


def test_parse_review_normalizes_missing_fields():
    rv = parse_review("x", "X", "mock", "m", '{"summary": "hi", "recommendation": "accept"}')
    assert rv.ok
    assert rv.payload["major_concerns"] == []
    assert rv.payload["ai_authorship"]["tells"] == []
    assert rv.payload["recommendation"] == "accept"


def test_parse_review_marks_unparseable():
    rv = parse_review("x", "X", "mock", "m", "definitely not json")
    assert not rv.ok and rv.error.startswith("parse:")


def test_mock_provider_returns_valid_schema_json():
    out = MockProvider().generate("sys", "usr", model="m", max_tokens=10, temperature=0.0)
    payload = json.loads(out)
    assert payload["scores"]["rigor"] == 3
    assert "ai_authorship" in payload


def test_get_provider_unknown():
    with pytest.raises(ProviderError):
        get_provider("nope")


def test_live_providers_require_keys(monkeypatch):
    # with no keys set, anthropic provider should raise a clear ProviderError
    for k in ("ANTHROPIC_API_KEY",):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(ProviderError):
        get_provider("anthropic").generate("s", "u", model="claude-opus-4-8",
                                           max_tokens=10, temperature=0.0)


def test_load_panel_three_reviewers_distinct_models():
    specs = load_panel()
    assert len(specs) == 3
    assert {s.provider for s in specs} == {"anthropic", "openai", "google"}
    assert all(s.system_prompt for s in specs)


def test_model_env_override(monkeypatch):
    monkeypatch.setenv("REVIEW_OPENAI_MODEL", "gpt-test-xyz")
    specs = {s.provider: s for s in load_panel()}
    assert specs["openai"].model == "gpt-test-xyz"


def test_load_dotenv_parses_and_respects_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('# comment\nexport OPENAI_API_KEY="sk-fromfile"\nGOOGLE_API_KEY=g123\n\n')
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "already-set")     # real env must win
    loaded = load_dotenv(env)
    assert "OPENAI_API_KEY" in loaded and "GOOGLE_API_KEY" not in loaded
    assert os.environ["OPENAI_API_KEY"] == "sk-fromfile"
    assert os.environ["GOOGLE_API_KEY"] == "already-set"


def test_load_dotenv_missing_file_is_noop(tmp_path):
    assert load_dotenv(tmp_path / "nope.env") == []


def test_build_context_notes_missing_file():
    out = ctxmod.build_context(["does/not/exist.md"])
    assert "FILE NOT FOUND" in out


def test_dry_run_orchestrator(tmp_path):
    record = run_panel(docs=["THEORY.md"], out_dir=tmp_path, dry_run=True)
    assert len(record["reviewers"]) == 3
    assert all(r["ok"] for r in record["reviewers"])
    run_dir = Path(record["run_dir"])
    assert (run_dir / "digest.md").exists()
    assert (run_dir / "run.json").exists()
    # each reviewer wrote a parseable result file
    for r in record["reviewers"]:
        data = json.loads((run_dir / f"{r['id']}.json").read_text())
        assert data["review"]["recommendation"] == "major_revision"
