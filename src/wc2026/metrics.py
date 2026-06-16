"""Predictability and forecast-quality metrics.

These are the paper's quantitative spine:
  * outcome entropy / surprisal  -> "how predictable is the tournament?"
  * competitive-balance index    -> spread of win probabilities
  * proper scoring rules (Brier, log-loss, RPS) -> forecast quality / calibration
Reviewers in this space reward proper scoring + calibration over raw accuracy.
"""
from __future__ import annotations

import math
from collections.abc import Sequence


def shannon_entropy(probs: Sequence[float], base: float = 2.0) -> float:
    """Entropy of an outcome distribution (e.g. champion probabilities).

    High entropy = unpredictable/open tournament; low = foregone conclusion.
    """
    return -sum(p * math.log(p, base) for p in probs if p > 0)


def surprisal(prob_of_observed: float, base: float = 2.0) -> float:
    """Self-information of the realized outcome; sums to a tournament 'shock' score."""
    return -math.log(max(prob_of_observed, 1e-12), base)


def brier_multiclass(probs: Sequence[float], outcome_index: int) -> float:
    """Multiclass Brier score for one match (lower is better)."""
    return sum((p - (1.0 if i == outcome_index else 0.0)) ** 2 for i, p in enumerate(probs))


def log_loss_single(probs: Sequence[float], outcome_index: int) -> float:
    return -math.log(max(probs[outcome_index], 1e-12))


def ranked_probability_score(probs: Sequence[float], outcome_index: int) -> float:
    """RPS for ordinal outcomes (home/draw/away). Standard in football forecasting."""
    cum_p, cum_o, total = 0.0, 0.0, 0.0
    for i, p in enumerate(probs):
        cum_p += p
        cum_o += 1.0 if i == outcome_index else 0.0
        total += (cum_p - cum_o) ** 2
    return total / (len(probs) - 1)


def competitive_balance_index(win_probs: Sequence[float]) -> float:
    """1 - normalized std of championship win probabilities across teams.

    1.0 = perfectly balanced field; ->0 = one dominant favorite.
    """
    n = len(win_probs)
    if n <= 1:
        return 0.0
    mean = sum(win_probs) / n
    var = sum((p - mean) ** 2 for p in win_probs) / n
    max_std = math.sqrt((1 - 1 / n) / n)   # std when one team has prob 1
    return 1.0 - (math.sqrt(var) / max_std if max_std > 0 else 0.0)
