"""Unit tests for the deterministic analytical core (metrics, manipulability)."""
import math

from src.wc2026 import metrics
from src.wc2026.manipulability import (
    TargetResult,
    is_manipulable,
    summarize,
    expansion_multiplier,
)


# ----- metrics -----------------------------------------------------------

def test_entropy_uniform_is_log_n():
    assert math.isclose(metrics.shannon_entropy([0.5, 0.5]), 1.0)
    assert math.isclose(metrics.shannon_entropy([1 / 3] * 3, base=3), 1.0)


def test_entropy_degenerate_is_zero():
    assert metrics.shannon_entropy([1.0, 0.0, 0.0]) == 0.0


def test_brier_perfect_forecast_is_zero():
    assert metrics.brier_multiclass([1.0, 0.0, 0.0], 0) == 0.0


def test_rps_rewards_ordinal_closeness():
    # predicting away when home happened is worse than predicting draw
    far = metrics.ranked_probability_score([0.0, 0.0, 1.0], 0)
    near = metrics.ranked_probability_score([0.0, 1.0, 0.0], 0)
    assert far > near


def test_competitive_balance_bounds():
    n = 8
    balanced = metrics.competitive_balance_index([1 / n] * n)
    dominant = metrics.competitive_balance_index([1.0] + [0.0] * (n - 1))
    assert math.isclose(balanced, 1.0, abs_tol=1e-9)
    assert math.isclose(dominant, 0.0, abs_tol=1e-9)


# ----- manipulability ----------------------------------------------------

class _StubEngine:
    """Engine where team 'TANKER' gains by losing in a cross-group state."""

    def advancement_value(self, team, state, target_result):
        if team == "TANKER":
            return {TargetResult.WIN: 0.4, TargetResult.DRAW: 0.5,
                    TargetResult.LOSE: 0.7}[target_result]
        return {TargetResult.WIN: 0.9, TargetResult.DRAW: 0.5,
                TargetResult.LOSE: 0.1}[target_result]

    def depends_on_other_groups(self, team, state):
        return team == "TANKER"


def test_manipulable_state_detected():
    eng = _StubEngine()
    r = is_manipulable(eng, "TANKER", state=None)
    assert r.manipulable
    assert r.adv_action is TargetResult.LOSE
    assert r.cross_group
    assert math.isclose(r.delta, 0.3)


def test_honest_team_not_manipulable():
    eng = _StubEngine()
    r = is_manipulable(eng, "HONEST", state=None)
    assert not r.manipulable
    assert r.delta == 0.0


def test_expansion_multiplier_and_summary():
    eng = _StubEngine()
    res48 = [is_manipulable(eng, t, None) for t in ("TANKER", "HONEST", "HONEST")]
    res32 = [is_manipulable(eng, t, None) for t in ("HONEST", "HONEST", "HONEST")]
    s48, s32 = summarize(res48), summarize(res32)
    assert math.isclose(s48.rho, 1 / 3)
    assert s48.cross_group_share == 1.0
    assert s32.rho == 0.0
    assert expansion_multiplier(s48, s32) == math.inf
