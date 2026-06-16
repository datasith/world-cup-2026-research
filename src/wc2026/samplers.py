"""Match samplers: turn a strength model into sampled scorelines.

The simulator needs *goal-level* outcomes (group ranking and the best-third-placed
rule both depend on goal difference and goals scored), so a W/D/L probability is
not enough. Both strength models expose a sampler here with a common interface:

    sample(home, away, neutral, rng) -> (home_goals, away_goals)

- PoissonSampler: native -- samples from the model's scoreline matrix.
- EloSampler: maps the Elo rating gap to a pair of Poisson goal rates, then
  samples. Lets us reproduce the whole analysis under a second, independent
  strength model for robustness (THEORY.md sec. 4).
"""
from __future__ import annotations

from typing import Protocol

import numpy as np


class MatchSampler(Protocol):
    def sample(self, home: str, away: str, neutral: bool,
               rng: np.random.Generator) -> tuple[int, int]:
        ...

    def expected_goals(self, home: str, away: str, neutral: bool) -> tuple[float, float]:
        ...


class PoissonSampler:
    """Samples scorelines from a fitted Bayesian Poisson model's score matrix."""

    def __init__(self, fit):
        self.fit = fit

    def expected_goals(self, home, away, neutral=True):
        return self.fit._rates(home, away, neutral)

    def sample(self, home, away, neutral, rng):
        lam_h, lam_a = self.fit._rates(home, away, neutral)
        return int(rng.poisson(lam_h)), int(rng.poisson(lam_a))


class EloSampler:
    """Maps Elo ratings to Poisson goal rates and samples scorelines.

    Calibrated so a rating-neutral match averages ``base_goals`` per side and the
    rate ratio tracks the win expectancy. Simple and transparent; ``base_goals``
    and ``spread`` can be fit to historical goal data later.
    """

    def __init__(self, model, base_goals: float = 1.35, spread: float = 0.95):
        self.model = model
        self.base_goals = base_goals
        self.spread = spread

    def expected_goals(self, home, away, neutral=True):
        e = self.model.expected_home(home, away, neutral=neutral)  # P(home not lose), in (0,1)
        # tilt goals toward the favorite while holding the total roughly fixed
        tilt = np.exp(self.spread * (e - 0.5))
        lam_h = self.base_goals * tilt
        lam_a = self.base_goals / tilt
        return float(lam_h), float(lam_a)

    def sample(self, home, away, neutral, rng):
        lam_h, lam_a = self.expected_goals(home, away, neutral)
        return int(rng.poisson(lam_h)), int(rng.poisson(lam_a))
