"""Time-varying Elo ratings and match-outcome probabilities.

A deliberately simple, transparent baseline that the ML layer must beat on
*calibration* (Brier / log-loss / RPS), not just accuracy. Includes a home
advantage term and a draw model so it emits full (home, draw, away) vectors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math


@dataclass
class EloModel:
    k: float = 30.0                 # update step size
    home_adv: float = 65.0          # Elo points added to the home side
    draw_width: float = 0.30        # controls draw probability vs. rating gap
    base: float = 1500.0
    ratings: dict[str, float] = field(default_factory=dict)

    def rating(self, team: str) -> float:
        return self.ratings.get(team, self.base)

    def expected_home(self, home: str, away: str, neutral: bool = False) -> float:
        """P(home does not lose), classic Elo logistic on the rating gap."""
        ha = 0.0 if neutral else self.home_adv
        gap = (self.rating(home) + ha) - self.rating(away)
        return 1.0 / (1.0 + 10 ** (-gap / 400.0))

    def outcome_probs(self, home: str, away: str, neutral: bool = False) -> tuple[float, float, float]:
        """Return calibrated (P_home, P_draw, P_away).

        Splits the Elo win-expectancy into win/draw/loss with a simple draw
        carve-out; ``draw_width`` should be fit to historical draw rates.
        """
        e = self.expected_home(home, away, neutral=neutral)
        p_draw = self.draw_width * (1.0 - abs(2 * e - 1))   # max draw when evenly matched
        p_home = e - p_draw / 2.0
        p_away = (1.0 - e) - p_draw / 2.0
        # clamp & renormalize for safety
        p = [max(1e-6, x) for x in (p_home, p_draw, p_away)]
        s = sum(p)
        return p[0] / s, p[1] / s, p[2] / s

    def update(self, home: str, away: str, home_goals: int, away_goals: int,
               neutral: bool = False) -> None:
        """Update ratings after a match (score = 1 win / 0.5 draw / 0 loss)."""
        if home_goals > away_goals:
            s = 1.0
        elif home_goals < away_goals:
            s = 0.0
        else:
            s = 0.5
        e = self.expected_home(home, away, neutral=neutral)
        # optional goal-difference multiplier (World Football Elo style)
        gd = abs(home_goals - away_goals)
        mult = math.log(max(gd, 1) + 1)
        delta = self.k * mult * (s - e)
        self.ratings[home] = self.rating(home) + delta
        self.ratings[away] = self.rating(away) - delta
