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
                n_inner: int = 120, max_iter: int = 12, seed: int = 0):
    """Best-response dynamics for a group's MD3 game.

    Returns (profile, status) where profile maps team -> equilibrium TargetResult and status
    is 'pure_NE' (fixed point reached) or 'no_pure_NE' (cycled within max_iter). Stochastic:
    payoffs are Monte-Carlo, so a clean fixed point is not guaranteed; raise n_inner for stability.
    """
    rng = np.random.default_rng(seed)
    md3 = group_matchdays(teams)[2]
    ds = {t: DecisionState(fixed=fixed, group_index=group_index, team=t, md3=md3) for t in teams}
    profile = {t: TargetResult.WIN for t in teams}

    for _ in range(max_iter):
        changed = False
        for team in teams:
            best_t, best_v = profile[team], float("-inf")
            for cand in TargetResult:
                trial = dict(profile); trial[team] = cand
                md3_results = _resolve_group(md3, trial, sampler=engine.sampler, rng=rng)
                v = engine.value_under_profile(team, ds[team], md3_results, n_inner=n_inner)
                if v > best_v:
                    best_v, best_t = v, cand
            if best_t is not profile[team]:
                profile[team] = best_t
                changed = True
        if not changed:
            return profile, "pure_NE"
    return profile, "no_pure_NE"


def equilibrium_manipulable(profile: dict) -> list[str]:
    """Teams whose equilibrium action is not WIN (manipulable under the equilibrium notion)."""
    return [t for t, a in profile.items() if a is not TargetResult.WIN]
