# Data sources

Catalog of historical + live data, with access notes and licensing. Nothing here is committed to
git in raw form — see `.gitignore`. Keep a provenance note for every dataset (source URL, retrieval
date, license) because Nature/PNAS require a Data Availability statement.

## Historical (32-team era and earlier)

| Dataset | Granularity | Coverage | Access | License/notes |
|---|---|---|---|---|
| `international-results` (Kaggle: martj42) | match results | 1872–present, all internationals | CSV download | Public domain-ish; cite |
| World Football Elo (eloratings.net) | team ratings over time | 1872–present | scrape / archived dumps | Attribution; check ToS |
| StatsBomb Open Data | event-level (passes, shots, xG) | incl. several World Cups | GitHub, free | Non-commercial research license — cite |
| FBref / Opta (via soccerdata pkg) | match + advanced stats | recent WCs | scrape | Personal/research use; rate-limit |
| FIFA/Kaggle "FIFA World Cup" tables | tournament structure, results | 1930–2022 | CSV | cite |

## Live 2026 (tournament under way; final ~2026-07-19)

| Source | What | Access | Notes |
|---|---|---|---|
| API-Football (api-football.com) | fixtures, live scores, lineups, stats | REST API, key | Free tier limited; paid for full |
| football-data.org | fixtures/results | REST API, key | Free tier OK for results |
| StatsBomb / Opta (if obtainable) | event-level for 2026 | partnership/paid | best for win-prob volatility metric |
| FIFA official | bracket, standings | scrape/manual | ground truth for results |

## Ingestion plan
- `scripts/fetch_historical.py` — pull + cache historical results and Elo into `data/raw/`.
- `scripts/fetch_live.py` — poll the live API on a schedule, append to `data/processed/live/`.
- All fetchers write a `*.provenance.json` (source, url, retrieved_at, license).

## Pre-registration freeze
When we lock predictions before the knockout stage, snapshot the exact training data + model hash
into `data/processed/prereg_freeze/` and tag the git commit.
