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
from .manipulability import ManipResult, TargetResult
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

    #: selectable advancement-value functional V_adv (THEORY.md sec. 2). All are
    #: estimated from the same sub-simulations; "depth" is the canonical definition.
    OBJECTIVES = ("depth", "qualify", "champion")

    def __init__(self, groups: list[list[str]], spec: FormatSpec,
                 sampler: MatchSampler, strength_rank: dict[str, int],
                 n_inner: int = 300, seed: int = 0, objective: str = "depth",
                 bracket: str = "seeded"):
        if objective not in self.OBJECTIVES:
            raise ValueError(f"objective must be one of {self.OBJECTIVES}")
        if bracket not in ("seeded", "official"):
            raise ValueError("bracket must be 'seeded' or 'official'")
        self.groups = groups
        self.spec = spec
        self.sampler = sampler
        self.strength_rank = strength_rank
        self.n_inner = n_inner
        self.objective = objective
        # "seeded": strength-seeded 1-vs-N stand-in (R4-R10). "official": the real fixed
        # 2026 R32->final bracket (bracket.py), valid only for the 12-group best-third format.
        self.bracket = bracket
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

    def _simulate_remainder(self, state: DecisionState,
                            team_score: tuple[int, int] | None,
                            extra_fixed: dict | None = None) -> tuple[int, bool, bool, bool]:
        """One full sub-simulation.

        Returns ``(knockout_depth, qualified, champion, qualified_via_best_third)``.
        ``team_score`` pins the team's own MD3 match (None to leave it to ``extra_fixed``
        or sampling). ``extra_fixed`` pins additional MD3 matches by (home,away)->score --
        used by the equilibrium solver to fix the *other* same-group match per a strategy
        profile (equilibrium.py)."""
        results_by_group: list[list[MatchResult]] = []
        th, ta = self._team_md3_match(state)
        for gi, teams in enumerate(self.groups):
            mds = group_matchdays(teams)
            res = []
            for md_idx, pairs in enumerate(mds):
                for h, a in pairs:
                    if (h, a) in state.fixed:                       # MD1-2 fixed (as keyed)
                        hg, ag = state.fixed[(h, a)]
                    elif (a, h) in state.fixed:                     # ... order-insensitive
                        ag, hg = state.fixed[(a, h)]
                    elif extra_fixed and (h, a) in extra_fixed:     # profile-pinned MD3 match
                        hg, ag = extra_fixed[(h, a)]
                    elif extra_fixed and (a, h) in extra_fixed:
                        ag, hg = extra_fixed[(a, h)]
                    elif (gi == state.group_index and (h, a) == (th, ta)
                          and team_score is not None):              # decision match
                        hg, ag = team_score
                    else:                                            # everything else sampled
                        hg, ag = self.sampler.sample(h, a, neutral=True, rng=self.rng)
                    res.append(MatchResult(h, a, hg, ag))
            results_by_group.append(res)

        # qualification (track group keys + finishing positions for the official bracket)
        group_keys = "ABCDEFGHIJKL"
        quals, thirds_bg = [], []          # thirds_bg: list of (group_key, TeamRecord)
        winner, runner = {}, {}
        team_finished_third = False
        for gi, teams in enumerate(self.groups):
            gk = group_keys[gi] if gi < len(group_keys) else str(gi)
            ranked = rank_group(teams, results_by_group[gi], rng=self.rng)
            for pos, rec in enumerate(ranked):
                if pos < self.spec.advance_top:
                    quals.append(rec.team)
                    if pos == 0:
                        winner[gk] = rec.team
                    elif pos == 1:
                        runner[gk] = rec.team
                elif pos == self.spec.advance_top and self.spec.best_thirds:
                    thirds_bg.append((gk, rec))
                    if rec.team == state.team:
                        team_finished_third = True
        best_thirds = []
        if self.spec.best_thirds:
            best_thirds = best_third_placed([rec for _, rec in thirds_bg], self.spec.best_thirds)
            quals.extend(best_thirds)

        if state.team not in quals:
            return 0, False, False, False        # depth, qualified, champion, via_third
        via_third = team_finished_third and state.team in quals

        if self.bracket == "official" and self.spec.best_thirds and len(self.groups) == 12:
            from . import bracket as bracket_mod
            team_group = {rec.team: gk for gk, rec in thirds_bg}
            qual_third_groups = [team_group[t] for t in best_thirds]
            slot_group = bracket_mod.assign_thirds(qual_third_groups)
            third_team_of_group = {team_group[t]: t for t in best_thirds}
            third_slot_team = {s: third_team_of_group[g] for s, g in slot_group.items()}
            leaf_teams = bracket_mod.build_leaf_teams(winner, runner, third_slot_team)
            champ, depths = bracket_mod.play(leaf_teams, self.sampler, self.rng)
            return depths.get(state.team, 0), True, champ == state.team, via_third

        seeded = sorted(quals, key=lambda t: self.strength_rank.get(t, 10**9))
        depth, champion = self._knockout_depth(seeded, state.team)
        return depth, True, champion, via_third

    def _knockout_depth(self, qualifiers_seeded: list[str], team: str) -> tuple[int, bool]:
        """Return (rounds the team survives, whether it wins the whole bracket)."""
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
        champion = len(bracket) == 1 and bracket[0] == team
        return depth, champion

    # --- manipulability contract ----------------------------------------
    def _evaluate_action(self, state: DecisionState, h: str, a: str,
                         team_is_home: bool, action: TargetResult) -> dict[str, float]:
        """Estimate all V_adv functionals for one action from shared sub-simulations.

        Returns means of: ``depth`` (knockout rounds won), ``qualify`` (P advance),
        ``champion`` (P win the title), and ``q3`` (P qualify via best-third)."""
        depth_sum = qual_sum = champ_sum = third_sum = 0.0
        for _ in range(self.n_inner):
            score = self._sample_conditioned(h, a, action, team_is_home)
            depth, qualified, champion, via_third = self._simulate_remainder(state, score)
            depth_sum += depth
            qual_sum += int(qualified)
            champ_sum += int(champion)
            third_sum += int(via_third)
        n = self.n_inner
        return {"depth": depth_sum / n, "qualify": qual_sum / n,
                "champion": champ_sum / n, "q3": third_sum / n}

    def advancement_value(self, team: str, state: DecisionState,
                          target_result: TargetResult) -> float:
        """Generic-contract entry (manipulability.is_manipulable): V_adv under the
        engine's configured ``objective``. ``assess`` is the efficient single-pass path."""
        h, a = self._team_md3_match(state)
        return self._evaluate_action(state, h, a, team == h, target_result)[self.objective]

    def value_under_profile(self, team: str, state: DecisionState,
                            md3_results: dict, n_inner: int | None = None) -> dict:
        """Mean V_adv and best-third rate for ``team`` when *both* MD3 matches of its group
        are pinned to ``md3_results`` ((home,away)->score) and all other groups are sampled.
        Returns {'depth': mean knockout rounds won, 'q3': P(qualify via best-third)}. The
        strategic primitive for the equilibrium solver (equilibrium.py)."""
        n = n_inner or self.n_inner
        total = third = 0.0
        for _ in range(n):
            depth, _q, _c, via_third = self._simulate_remainder(state, None, extra_fixed=md3_results)
            total += depth
            third += int(via_third)
        return {"depth": total / n, "q3": third / n}

    def assess(self, team: str, state: DecisionState, min_delta: float = 0.05,
               q3_threshold: float = 0.05) -> ManipResult:
        """Single-pass manipulability assessment with a *measured* cross-group flag.

        A manipulable state is classified **cross-group** when, under the
        advancement-optimal action, the team has non-trivial probability
        (> ``q3_threshold``) of qualifying via the best-third-placed pool -- the
        route that depends on other groups and that within-group simultaneity
        cannot neutralize. In the 32-team format this probability is identically
        zero (no best-third pool), so cross-group is structurally False there.
        """
        h, a = self._team_md3_match(state)
        team_is_home = (team == h)
        values: dict[TargetResult, float] = {}
        q3: dict[TargetResult, float] = {}
        for action in TargetResult:
            res = self._evaluate_action(state, h, a, team_is_home, action)
            values[action], q3[action] = res[self.objective], res["q3"]
        adv_action = max(values, key=values.get)
        win_val = values[TargetResult.WIN]
        delta = max(0.0, values[adv_action] - win_val)
        manipulable = adv_action is not TargetResult.WIN and delta > min_delta
        cross_group = manipulable and q3[adv_action] > q3_threshold
        return ManipResult(
            team=team,
            manipulable=manipulable,
            win_action=TargetResult.WIN,
            adv_action=adv_action,
            delta=delta,
            cross_group=cross_group,
            q3_adv=q3[adv_action],
        )
