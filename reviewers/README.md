# Reviewer panel (LLM-as-judge)

Three expert-persona reviewers, each on a **different model family**, critique the
manuscript and supporting documents — to surface blind spots, inconsistencies, weak
claims, missing prior art, and **AI-generated prose** — so we can improve the work before
submission. Personas are kept as editable markdown (prompt-as-data); edit them freely.

| Reviewer | Persona | Provider | Model (verified 2026-06-17) |
|----------|---------|----------|------------------------------|
| R1 — The Theorist | `personas/theorist.md` (mechanism design / social choice) | anthropic | `claude-opus-4-8` |
| R2 — The Domain Skeptic | `personas/domain_skeptic.md` (tournament-design OR) | openai | `gpt-5.5` |
| R3 — The Methodologist | `personas/methodologist.md` (Bayesian stats / meta-science) | google | `gemini-3.1-pro-preview` |

Model ids live in `config.json` and are overridable per provider via
`REVIEW_<PROVIDER>_MODEL` (e.g. `gemini-2.5-pro` is the stable Gemini fallback).

## Setup

```bash
uv pip install -e '.[review]'          # anthropic, openai, google-genai
cp .env.example .env && chmod 600 .env # then paste your keys into .env
```

### Keys — permanent & secure (no session exports)

Put keys in a **`.env` file at the repo root**. It is gitignored and auto-loaded on every
run (`src/wc2026/review/env.py`), so it survives crashes, new shells, and reboots — no
fragile `export`s. Real shell env vars still override the file (handy for CI); `chmod 600`
keeps it readable only by you.

How to get each key (every console lets you name, scope, and revoke keys):

| Reviewer | Var | Where | Notes |
|---|---|---|---|
| R1 Theorist | `ANTHROPIC_API_KEY` | console.anthropic.com → **Settings → API keys → Create key** | needs billing/credits |
| R2 Domain Skeptic | `OPENAI_API_KEY` | platform.openai.com → **API keys → Create new secret key** | shown once — copy now; scope to a project |
| R3 Methodologist | `GOOGLE_API_KEY` | aistudio.google.com → **Get API key → Create API key** | `GEMINI_API_KEY` also accepted |

Then fill `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GOOGLE_API_KEY=AIza...
# optional model pins:
# REVIEW_OPENAI_MODEL=gpt-5.5
# REVIEW_GOOGLE_MODEL=gemini-3.1-pro-preview
```

> Never commit real keys. Only `.env.example` (placeholders) is tracked; `.env` is ignored.
> For stronger hardening, keep keys in your OS keychain and export them in your shell — the
> loader will then find them already in the environment and leave them as-is.

## Run

```bash
uv run python scripts/run_review.py            # full panel (needs keys)
uv run python scripts/run_review.py --dry-run  # offline mock, no keys (CI / smoke)
uv run python scripts/run_review.py --docs paper/main.tex THEORY.md
```

Output lands in `results/reviews/<timestamp>/`: one `<reviewer>.json` per reviewer
(structured critique incl. `ai_authorship`), `run.json` (provenance), and `digest.md`
(human-readable cross-reviewer summary). These run outputs are gitignored.

## Schema & extending

The structured output contract is `src/wc2026/review/schema.py`
(`REVIEW_JSON_SCHEMA`). Shared instructions live in `rubric.md`; per-reviewer expertise in
`personas/*.md`. Add a reviewer by adding a persona file + a `config.json` entry; add a
model family by implementing a `Provider` in `src/wc2026/review/providers.py`.
