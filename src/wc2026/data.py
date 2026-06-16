"""Load and normalize historical international results.

Reads the martj42 results CSV fetched by scripts/fetch_historical.py and exposes
tidy frames plus helpers to slice the World Cup eras we compare (32-team era vs
prior formats) and to filter the training window for the strength models.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data"
RAW = DATA / "raw"
RESULTS_CSV = RAW / "international_results.csv"
DRAW_2026 = DATA / "draw_2026.json"

# Country-name aliases that drift across the historical record. Extend as needed
# so a team's rating is continuous through renames.
ALIASES = {
    "West Germany": "Germany",
    "East Germany": "Germany DR",
    "Soviet Union": "Russia",
    "Czechoslovakia": "Czech Republic",
    "Yugoslavia": "Serbia",
    "Zaire": "DR Congo",
    "Republic of Ireland": "Ireland",
}


def load_results(path: Path = RESULTS_CSV) -> pd.DataFrame:
    """Return tidy match results with parsed dates and normalized team names.

    Columns: date, home_team, away_team, home_score, away_score, tournament,
    city, country, neutral (bool), plus year.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found - run: uv run python scripts/fetch_historical.py"
        )
    df = pd.read_csv(path, parse_dates=["date"])
    for col in ("home_team", "away_team"):
        df[col] = df[col].replace(ALIASES)
    df["neutral"] = df["neutral"].astype(bool)
    df["year"] = df["date"].dt.year
    df = df.dropna(subset=["home_score", "away_score"]).reset_index(drop=True)
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    return df


def world_cups(df: pd.DataFrame) -> pd.DataFrame:
    """Matches played at FIFA World Cup final tournaments."""
    return df[df["tournament"] == "FIFA World Cup"].copy()


def era_32_team(df: pd.DataFrame) -> pd.DataFrame:
    """World Cup matches in the 32-team era (1998-2022 inclusive)."""
    wc = world_cups(df)
    return wc[(wc["year"] >= 1998) & (wc["year"] <= 2022)].copy()


def load_draw(path: Path = DRAW_2026) -> dict:
    """Load the official 2026 draw: {'groups': {A: [...]}, 'results': [...]}.

    Returns groups as an ordered list-of-lists (A..L) plus the played results as
    MatchResult-shaped dicts, using martj42 team spellings.
    """
    with open(path) as fh:
        raw = json.load(fh)
    keys = sorted(raw["groups"])
    groups = [raw["groups"][k] for k in keys]
    schedule = {k: raw.get("schedule", {}).get(k) for k in keys}
    return {"groups": groups, "results": raw["results"],
            "schedule": schedule, "meta": raw.get("_provenance", {})}


def training_window(df: pd.DataFrame, since: str = "2018-01-01",
                    until: str | None = None) -> pd.DataFrame:
    """Recent internationals for fitting current-strength models.

    Defaults to a post-2018 window (recent enough that current squads are
    represented). ``until`` lets us reproduce the pre-registration freeze.
    """
    out = df[df["date"] >= pd.Timestamp(since)]
    if until is not None:
        out = out[out["date"] <= pd.Timestamp(until)]
    return out.reset_index(drop=True)
