"""Manipulability engine: values final-matchday decisions by sub-simulation.

Implements the contract in manipulability.py on top of the simulator. The state
of interest is a group's **final matchday** (MD3): matchdays 1-2 of every group
are fixed; a team is about to play its MD3 game (simultaneous with the other
game in its group). We value each target result (win/draw/lose) by conditioning
the team's match and Monte-Carlo simulating the remainder of the tournament,
scoring the team's expected knockout depth (rounds won). When the result-maximizing
action is *not* WIN, the state is manipulable (THEORY.md sec. 2).

``depends_on_other_groups`` is the structural discriminator: under the 48-team
format a team in third place can still qualify via the best-third pool, which
depends on *other groups* and is therefore immune to within-group simultaneity.
Under the 32-team format there is no such pool, so it is always False.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .formats import (
    FormatSpec,
    MatchResult,
    best_third_placed,
    group_matchdays,
    rank_group,
)
from .manipulability import TargetResult
from .samplers import MatchSampler
from .simulator import play_knockout

_FORCE = {TargetResult.WIN: (1, 0), TargetResult.DRAW: (0, 0), TargetResult.LOSE: (0, 1)}


def _matches_target(hg: int, ag: int, target: TargetResult) -> bool:
    if target is TargetResult.WIN:
        return hg > ag
    if target is TargetResult.DRAW:
        return hg == ag
    return hg < ag


@dataclass
class DecisionState:
    """A team's MD3 decision within a fixed pre-MD3 tournament snapshot."""
    fixed: dict[tuple[str, str], tuple[int, int]]   # all MD1-2 results, every group
    group_index: int
    team: str
    md3: list[tuple[str, str]]                       # the two MD3 pairings in this group


class SimEngine:
    """Engine consumed by manipulability.is_manipulable."""

    def __init__(self, groups: list[list[str]], spec: FormatSpec,
                 sampler: MatchSampler, strength_rank: dict[str, int],
                 n_inner: int = 300, seed: int = 0):
        self.groups = groups
        self.spec = spec
        self.sampler = sampler
        self.strength_rank = strength_rank
        self.n_inner = n_inner
        self.rng = np.random.default_rng(seed)

    # --- helpers ---------------------------------------------------------
    def _team_md3_match(self, state: DecisionState) -> tuple[str, str]:
        for h, a in state.md3:
            if state.team in (h, a):
                return h, a
        raise ValueError("team not in its MD3 pairings")

    def _sample_conditioned(self, h: str, a: str, target: TargetResult,
                            team_is_home: bool) -> tuple[int, int]:
        """Sample a scoreline for the team's match consistent with its target."""
        # express target from the home side's perspective
        home_target = target
        if not team_is_home:
            home_target = {TargetResult.WIN: TargetResult.LOSE,
                           TargetResult.LOSE: TargetResult.WIN,
                           TargetResult.DRAW: TargetResult.DRAW}[target]
        for _ in range(50):
            hg, ag = self.sampler.sample(h, a, neutral=True, rng=self.rng)
            if _matches_target(hg, ag, home_target):
                return hg, ag
        return _FORCE[home_target]

    def _simulate_remainder(self, state: DecisionState, team_score: tuple[int, int]) -> int:
        """One full sub-simulation; return knockout rounds the team wins (>=0)."""
        results_by_group: list[list[MatchResult]] = []
        th, ta = self._team_md3_match(state)
        for gi, teams in enumerate(self.groups):
            mds = group_matchdays(teams)
            res = []
            for md_idx, pairs in enumerate(mds):
                for h, a in pairs:
                    if (h, a) in state.fixed:                       # MD1-2 fixed
                        hg, ag = state.fixed[(h, a)]
                    elif gi == state.group_index and (h, a) == (th, ta):  # decision match
                        hg, ag = team_score
                    else:                                            # everything else sampled
                        hg, ag = self.sampler.sample(h, a, neutral=True, rng=self.rng)
                    res.append(MatchResult(h, a, hg, ag))
            results_by_group.append(res)

        # qualification
        quals, thirds = [], []
        for gi, teams in enumerate(self.groups):
            ranked = rank_group(teams, results_by_group[gi], rng=self.rng)
            for pos, rec in enumerate(ranked):
                if pos < self.spec.advance_top:
                    quals.append(rec.team)
                elif pos == self.spec.advance_top and self.spec.best_thirds:
                    thirds.append(rec)
        if self.spec.best_thirds:
            quals.extend(best_third_placed(thirds, self.spec.best_thirds))

        if state.team not in quals:
            return 0
        seeded = sorted(quals, key=lambda t: self.strength_rank.get(t, 10**9))
        # expected knockout depth: replay bracket, count rounds the team survives
        return self._knockout_depth(seeded, state.team)

    def _knockout_depth(self, qualifiers_seeded: list[str], team: str) -> int:
        from .simulator import _seed_bracket, _knockout_winner
        bracket = _seed_bracket(qualifiers_seeded)
        depth = 0
        while len(bracket) > 1 and team in bracket:
            nxt = []
            for i in range(0, len(bracket), 2):
                nxt.append(_knockout_winner(bracket[i], bracket[i + 1], self.sampler, self.rng))
            if team in nxt:
                depth += 1
            bracket = nxt
        return depth

    # --- manipulability contract ----------------------------------------
    def advancement_value(self, team: str, state: DecisionState,
                          target_result: TargetResult) -> float:
        h, a = self._team_md3_match(state)
        team_is_home = (team == h)
        total = 0.0
        for _ in range(self.n_inner):
            score = self._sample_conditioned(h, a, target_result, team_is_home)
            total += self._simulate_remainder(state, score)
        return total / self.n_inner

    def depends_on_other_groups(self, team: str, state: DecisionState) -> bool:
        """True iff a third-place finish could still qualify the team (48-team
        best-third pool). Structurally False for the 32-team format."""
        return self.spec.best_thirds > 0
