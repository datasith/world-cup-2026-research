"""Equilibrium treatment of the group finale (addressing reviewer R1).

The primary analysis (engine.assess) is *decision-theoretic*: a team's best response when
all other matches are sampled from the fixed strength model. But a group's two final-matchday
matches are played simultaneously and all four teams are strategic. Here we treat the group
finale as a simultaneous-move game and find pure-strategy Nash equilibria by best-response
dynamics, so we can ask whether the manipulability flag -- and especially the cross-group
share -- survives the equilibrium notion (THEORY.md sec. 4.3).

Strategies. Each team picks a target result for its own match, in {WIN, DRAW, LOSE}.
Match resolution (the modelling choice that also captures Gijon-style collusion): for a match
(h, a) with targets t_h, t_a, if the two teams' *desired results coincide* (e.g. one targets
WIN and the other LOSE toward the same side, or both target DRAW) that result is realised
deterministically (a minimal scoreline); otherwise the targets conflict and the match is a
genuine contest, sampled from the strength model.

Payoffs are V_adv (expected knockout rounds won, engine.value_under_profile): both group
matches pinned by the profile, all other groups sampled, official/seeded bracket per the engine.
"""
from __future__ import annotations

import numpy as np

from .engine import DecisionState, SimEngine
from .formats import group_matchdays
from .manipulability import TargetResult

# minimal scorelines for a deterministically-realised (collusion-feasible) result
_HOME, _DRAW, _AWAY = (1, 0), (0, 0), (0, 1)


def _desired(target: TargetResult, is_home: bool) -> str:
    """The match result a team wants given its target: 'H' home win, 'X' draw, 'A' away win."""
    if target is TargetResult.DRAW:
        return "X"
    win_side = "H" if is_home else "A"
    lose_side = "A" if is_home else "H"
    return win_side if target is TargetResult.WIN else lose_side


def resolve_match(h: str, a: str, t_h: TargetResult, t_a: TargetResult,
                  sampler, rng: np.random.Generator) -> tuple[int, int]:
    """Resolve one match from both teams' targets (see module docstring)."""
    d_h, d_a = _desired(t_h, True), _desired(t_a, False)
    if d_h == d_a:                       # mutual interest -> realised (collusion-feasible)
        return {"H": _HOME, "X": _DRAW, "A": _AWAY}[d_h]
    return sampler.sample(h, a, neutral=True, rng=rng)   # conflict -> genuine contest


def _resolve_group(md3, profile, sampler, rng) -> dict:
    """Resolve both MD3 matches of a group from a strategy profile -> {(h,a): (hg,ag)}."""
    out = {}
    for h, a in md3:
        out[(h, a)] = resolve_match(h, a, profile[h], profile[a], sampler, rng)
    return out


def solve_group(engine: SimEngine, group_index: int, teams: list[str], fixed: dict,
                n_inner: int = 200, max_iter: int = 12, min_improve: float = 0.03, seed: int = 0):
    """Best-response dynamics for a group's MD3 game.

    Returns (profile, status). A team deviates from its current action only if some alternative
    beats it by more than ``min_improve`` (in V_adv = knockout rounds) -- a significance margin
    tied to Monte-Carlo noise that prevents payoff noise from causing endless flip-flopping and
    keeps WIN "sticky" (a team is flagged manipulable only on a clear gain, mirroring the
    decision-theoretic margin). Status is 'pure_NE' (fixed point) or 'no_pure_NE' (cycled).
    """
    rng = np.random.default_rng(seed)
    md3 = group_matchdays(teams)[2]
    ds = {t: DecisionState(fixed=fixed, group_index=group_index, team=t, md3=md3) for t in teams}
    profile = {t: TargetResult.WIN for t in teams}

    for _ in range(max_iter):
        changed = False
        for team in teams:
            vals = {}
            for cand in TargetResult:
                trial = dict(profile); trial[team] = cand
                md3_results = _resolve_group(md3, trial, sampler=engine.sampler, rng=rng)
                vals[cand] = engine.value_under_profile(team, ds[team], md3_results, n_inner=n_inner)["depth"]
            best = max(vals, key=vals.get)
            if best is not profile[team] and vals[best] > vals[profile[team]] + min_improve:
                profile[team] = best
                changed = True
        if not changed:
            return profile, "pure_NE"
    return profile, "no_pure_NE"


def classify(engine: SimEngine, group_index: int, teams: list[str], fixed: dict,
             profile: dict, n_inner: int = 200, q3_threshold: float = 0.05, seed: int = 1):
    """Given an equilibrium profile, return per-team (manipulable, cross_group) flags.

    A team is equilibrium-manipulable if its equilibrium action != WIN; cross-group if, under the
    equilibrium profile, it qualifies via the best-third pool with probability > q3_threshold."""
    rng = np.random.default_rng(seed)
    md3 = group_matchdays(teams)[2]
    md3_results = _resolve_group(md3, profile, sampler=engine.sampler, rng=rng)
    out = {}
    for t in teams:
        manip = profile[t] is not TargetResult.WIN
        q3 = 0.0
        if manip:
            ds = DecisionState(fixed=fixed, group_index=group_index, team=t, md3=md3)
            q3 = engine.value_under_profile(t, ds, md3_results, n_inner=n_inner)["q3"]
        out[t] = {"manipulable": manip, "cross_group": manip and q3 > q3_threshold, "q3": q3}
    return out


def equilibrium_manipulable(profile: dict) -> list[str]:
    """Teams whose equilibrium action is not WIN (manipulable under the equilibrium notion)."""
    return [t for t, a in profile.items() if a is not TargetResult.WIN]
