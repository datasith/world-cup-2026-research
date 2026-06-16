# World Cup 2026: a natural experiment in tournament design

Research project analyzing how the FIFA World Cup's expansion from 32 to 48 teams reshapes the
**predictability, luck, and competitive stakes** of the tournament, using historical data, a
calibrated strength/ML model, and a Monte Carlo tournament simulator — with **pre-registered live
predictions** scored against the ongoing 2026 tournament (final ~2026-07-19).

> Target: design for *Nature Human Behaviour / PNAS*, written so the lead result could reach
> *Nature/Science*. See [`DESIGN.md`](DESIGN.md) for the full research plan, literature scan, and
> the ranked candidate angles.

## Layout
```
DESIGN.md            research plan, literature gap, angles, open decisions
data/                source catalog (README) + raw/processed (gitignored)
src/wc2026/          library: ingestion, strength models, simulator, metrics
scripts/             runnable fetchers + pipelines
notebooks/           exploratory analysis
paper/               LaTeX manuscript (Nature-style skeleton) + refs
```

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Status
Scaffolding. Next: lock the lead angle (see open decisions in `DESIGN.md`), wire historical
ingestion, build the Elo/Poisson baseline + simulator.
