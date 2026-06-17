"""Manipulability / strategyproofness analysis (lead result).

Implements the definitions in THEORY.md:
  * V_adv(team, state, action)  - expected progression value of a target result
  * is_manipulable(team, state) - advancement-optimal action != win-optimal action
  * format-level statistics      - rate rho, mass Delta-bar, cross-group share

Depends on a tournament simulator that can, from a partial state, estimate each
team's progression probability conditional on a chosen match result. The action
space is the set of *target result distributions* a team can rationally aim for
(win / draw / lose, and scoreline bands where relevant), NOT exact scores.

Everything here is engine-agnostic: pass any object exposing
``advancement_value(team, state, target_result) -> float``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TargetResult(Enum):
    """Coarse action space for a team in its current match."""
    WIN = "win"
    DRAW = "draw"
    LOSE = "lose"


@dataclass(frozen=True)
class ManipResult:
    team: str
    manipulable: bool
    win_action: TargetResult          # action maximizing P(win this match)
    adv_action: TargetResult          # action maximizing progression value
    delta: float                      # forgone progression value if playing to win
    cross_group: bool                 # dependency is on other groups (simultaneity-proof)
    q3_adv: float = 0.0               # raw P(qualify via best-third) under adv_action;
                                      # lets thresholds be swept post-hoc (sensitivity)


def advancement_optimal(engine, team: str, state) -> tuple[TargetResult, float]:
    """Return the target result maximizing progression value, and that value."""
    best_action, best_val = TargetResult.WIN, float("-inf")
    for action in TargetResult:
        v = engine.advancement_value(team, state, action)
        if v > best_val:
            best_action, best_val = action, v
    return best_action, best_val


def is_manipulable(engine, team: str, state, min_delta: float = 0.0) -> ManipResult:
    """Evaluate manipulability of ``state`` for ``team`` (see THEORY.md sec. 2).

    ``win_action`` is WIN by construction (winning the match is always the
    match-win-maximizing target); a state is manipulable when the
    progression-optimal action differs and yields strictly more value.
    ``min_delta`` is a noise margin: when advancement values are Monte-Carlo
    estimates, require the gain to exceed it before flagging manipulability.
    """
    adv_action, adv_val = advancement_optimal(engine, team, state)
    win_val = engine.advancement_value(team, state, TargetResult.WIN)
    delta = max(0.0, adv_val - win_val)
    manipulable = adv_action is not TargetResult.WIN and delta > min_delta
    cross_group = manipulable and engine.depends_on_other_groups(team, state)
    return ManipResult(
        team=team,
        manipulable=manipulable,
        win_action=TargetResult.WIN,
        adv_action=adv_action,
        delta=delta,
        cross_group=cross_group,
    )


@dataclass
class FormatManipStats:
    rho: float                 # P(state manipulable for some team)
    delta_bar: float           # mean manipulability mass over manipulable states
    cross_group_share: float   # fraction of manipulable states that are simultaneity-proof
    n_states: int


def summarize(results: list[ManipResult]) -> FormatManipStats:
    """Aggregate per-state ManipResults into format-level statistics."""
    n = len(results)
    if n == 0:
        return FormatManipStats(0.0, 0.0, 0.0, 0)
    manip = [r for r in results if r.manipulable]
    rho = len(manip) / n
    delta_bar = sum(r.delta for r in manip) / len(manip) if manip else 0.0
    cross_share = sum(r.cross_group for r in manip) / len(manip) if manip else 0.0
    return FormatManipStats(rho, delta_bar, cross_share, n)


def expansion_multiplier(stats_48: FormatManipStats, stats_32: FormatManipStats) -> float:
    """The headline number: how much expansion scales the manipulability rate."""
    if stats_32.rho == 0:
        return float("inf")
    return stats_48.rho / stats_32.rho
