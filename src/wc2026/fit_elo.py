"""Fit time-varying Elo ratings by replaying history chronologically.

Walks every international in date order, updating an EloModel. Optionally scores
out-of-sample forecast quality (RPS / log-loss) on a held-out window so we can
report calibration against the Bayesian model on equal footing.
"""
from __future__ import annotations

import pandas as pd

from .elo import EloModel
from .metrics import log_loss_single, ranked_probability_score


def _outcome_index(home_score: int, away_score: int) -> int:
    """0=home win, 1=draw, 2=away win (matches outcome_probs ordering)."""
    if home_score > away_score:
        return 0
    if home_score == away_score:
        return 1
    return 2


def fit(results: pd.DataFrame, model: EloModel | None = None,
        score_since: str | None = None) -> tuple[EloModel, dict]:
    """Replay ``results`` chronologically; return the fitted model and metrics.

    If ``score_since`` is given, matches on/after that date are scored
    out-of-sample (predicted with the rating *before* the update) and the mean
    RPS / log-loss are returned.
    """
    model = model or EloModel()
    df = results.sort_values("date")
    score_from = pd.Timestamp(score_since) if score_since else None

    rps_sum = ll_sum = 0.0
    n_scored = 0
    for row in df.itertuples(index=False):
        if score_from is not None and row.date >= score_from:
            probs = model.outcome_probs(row.home_team, row.away_team, neutral=row.neutral)
            idx = _outcome_index(row.home_score, row.away_score)
            rps_sum += ranked_probability_score(probs, idx)
            ll_sum += log_loss_single(probs, idx)
            n_scored += 1
        model.update(row.home_team, row.away_team,
                     row.home_score, row.away_score, neutral=row.neutral)

    metrics = {
        "n_matches": len(df),
        "n_teams": len(model.ratings),
        "n_scored": n_scored,
        "mean_rps": rps_sum / n_scored if n_scored else None,
        "mean_log_loss": ll_sum / n_scored if n_scored else None,
    }
    return model, metrics


def top_ratings(model: EloModel, n: int = 20) -> pd.DataFrame:
    s = pd.Series(model.ratings).sort_values(ascending=False).head(n)
    return s.rename("elo").rename_axis("team").reset_index()
