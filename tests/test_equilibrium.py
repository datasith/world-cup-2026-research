"""Tests for the group-finale equilibrium solver (src/wc2026/equilibrium.py)."""
from __future__ import annotations

import numpy as np

from src.wc2026 import equilibrium as eq
from src.wc2026.manipulability import TargetResult as T


class FixedSampler:
    """Deterministic sampler: any contested match returns (3, 1)."""
    def sample(self, h, a, neutral, rng):
        return (3, 1)
    def expected_goals(self, h, a, neutral=True):
        return (1.0, 1.0)


def test_desired_results():
    assert eq._desired(T.WIN, is_home=True) == "H"
    assert eq._desired(T.LOSE, is_home=True) == "A"
    assert eq._desired(T.WIN, is_home=False) == "A"
    assert eq._desired(T.LOSE, is_home=False) == "H"
    assert eq._desired(T.DRAW, is_home=True) == "X"
    assert eq._desired(T.DRAW, is_home=False) == "X"


def test_mutual_interest_is_realized_deterministically():
    rng = np.random.default_rng(0)
    s = FixedSampler()
    # both want a draw
    assert eq.resolve_match("P", "Q", T.DRAW, T.DRAW, s, rng) == (0, 0)
    # home wants win, away wants to lose -> both want home win
    assert eq.resolve_match("P", "Q", T.WIN, T.LOSE, s, rng) == (1, 0)
    # home wants to lose, away wants win -> both want away win
    assert eq.resolve_match("P", "Q", T.LOSE, T.WIN, s, rng) == (0, 1)


def test_conflicting_targets_go_to_contest():
    rng = np.random.default_rng(0)
    s = FixedSampler()
    # both target WIN -> conflict -> sampled (3,1)
    assert eq.resolve_match("P", "Q", T.WIN, T.WIN, s, rng) == (3, 1)
    # home WIN, away DRAW -> conflict (H vs X) -> sampled
    assert eq.resolve_match("P", "Q", T.WIN, T.DRAW, s, rng) == (3, 1)


def test_resolve_group_covers_both_matches():
    rng = np.random.default_rng(0)
    md3 = [("A", "B"), ("C", "D")]
    profile = {"A": T.DRAW, "B": T.DRAW, "C": T.WIN, "D": T.LOSE}
    out = eq._resolve_group(md3, profile, FixedSampler(), rng)
    assert out[("A", "B")] == (0, 0)      # mutual draw
    assert out[("C", "D")] == (1, 0)      # both want C win


def test_equilibrium_manipulable_lists_nonwin():
    profile = {"A": T.WIN, "B": T.DRAW, "C": T.LOSE, "D": T.WIN}
    assert set(eq.equilibrium_manipulable(profile)) == {"B", "C"}
