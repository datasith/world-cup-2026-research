"""Monte Carlo tournament simulator (stub).

Goal: given a strength model that emits match-outcome probabilities, simulate a
full tournament many times under a chosen FORMAT (32-team: 8 groups of 4, or
48-team 2026: 12 groups of 4 + best-third qualifiers), returning the
distribution of champions, round-reach probabilities, and per-match stakes.

This is the engine behind the "expansion paradox" and "luck of the draw"
analyses: hold team strengths fixed, vary the format and/or the draw, compare
outcome-entropy and draw-luck attribution across formats.

TODO:
  * implement group stage + knockout bracket for both formats
  * best-third-placed qualifier logic for the 48-team format
  * draw resampling to isolate bracket luck
  * per-match 'stakes' flag (does the result affect advancement?)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Format:
    name: str
    n_teams: int
    n_groups: int
    group_size: int
    advance_per_group: int
    extra_qualifiers: int = 0   # e.g. 8 best third-placed in WC2026


FORMAT_32 = Format("WC2018/2022", n_teams=32, n_groups=8, group_size=4, advance_per_group=2)
FORMAT_48 = Format("WC2026", n_teams=48, n_groups=12, group_size=4,
                   advance_per_group=2, extra_qualifiers=8)


def simulate(model, teams, fmt: Format, n_sims: int = 10000, seed: int | None = None):
    """Run ``n_sims`` tournaments; return aggregated outcome statistics.

    Parameters
    ----------
    model : object with ``outcome_probs(home, away, neutral=True)``
    teams : sequence of team identifiers (len == fmt.n_teams)
    fmt   : a Format describing structure
    """
    raise NotImplementedError("simulator core to be implemented after angle lock-in")


class Engine:
    """Adapter the manipulability analysis consumes (see manipulability.py).

    A built-out simulator instance must implement this contract so that, from a
    partial tournament state, we can value a team's target result and detect
    cross-group dependencies. Stubbed until the simulator core lands.
    """

    def advancement_value(self, team: str, state, target_result) -> float:
        """Expected progression value for ``team`` if it aims for ``target_result``
        from ``state`` (probability-weighted value of advancing, incl. the strength
        of the likely knockout path). See THEORY.md sec. 2."""
        raise NotImplementedError

    def depends_on_other_groups(self, team: str, state) -> bool:
        """True iff ``team``'s required result in ``state`` depends on results in
        OTHER groups (the best-third-placed cross-group dependency that within-group
        simultaneous kickoffs cannot neutralize)."""
        raise NotImplementedError
