# Reviewer panel (LLM-as-judge)

Three expert-persona reviewers, each on a **different model family**, critique the
manuscript and supporting documents — to surface blind spots, inconsistencies, weak
claims, missing prior art, and **AI-generated prose** — so we can improve the work before
submission. Personas are kept as editable markdown (prompt-as-data); edit them freely.

| Reviewer | Persona | Provider | Default model |
|----------|---------|----------|---------------|
| R1 — The Theorist | `personas/theorist.md` (mechanism design / social choice) | anthropic | `claude-opus-4-8` |
| R2 — The Domain Skeptic | `personas/domain_skeptic.md` (tournament-design OR) | openai | `gpt-5.1` * |
| R3 — The Methodologist | `personas/methodologist.md` (Bayesian stats / meta-science) | google | `gemini-2.5-pro` * |

\* The OpenAI/Gemini model ids in `config.json` are **placeholders** — set them to the
latest ids you have access to, either by editing `config.json` or via env override.

## Setup

```bash
uv pip install -e '.[review]'          # anthropic, openai, google-genai

export ANTHROPIC_API_KEY=...           # R1
export OPENAI_API_KEY=...              # R2
export GOOGLE_API_KEY=...              # R3  (GEMINI_API_KEY also accepted)

# optional: pin the latest models without editing config.json
export REVIEW_OPENAI_MODEL=gpt-5.1
export REVIEW_GOOGLE_MODEL=gemini-2.5-pro
```

Keys are read from the environment only — never put them in `config.json` or code.

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
