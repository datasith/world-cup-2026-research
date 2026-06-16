"""Tournament structure: groups, FIFA ranking, and qualification rules.

Covers both formats we contrast:
  * 32-team (1998-2022): 8 groups of 4, top 2 advance -> Round of 16.
  * 48-team (2026):       12 groups of 4, top 2 + 8 best third-placed -> Round of 32.

FIFA group ranking order (World Cup): (1) points, (2) goal difference,
(3) goals scored, then (4) head-to-head among still-level teams. We implement
1-3 plus a head-to-head mini-table for exact ties; the remaining FIFA criteria
(fair play, drawing of lots) are resolved by a seeded RNG so results are
reproducible. The official R32 pairing table for best-third slots can be slotted
into ``knockout_seeding`` later; we use a consistent seeded bracket meanwhile.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations

WIN, DRAW = 3, 1


@dataclass
class MatchResult:
    home: str
    away: str
    hg: int
    ag: int


@dataclass
class TeamRecord:
    team: str
    played: int = 0
    points: int = 0
    gf: int = 0
    ga: int = 0

    @property
    def gd(self) -> int:
        return self.gf - self.ga

    def add(self, scored: int, conceded: int) -> None:
        self.played += 1
        self.gf += scored
        self.ga += conceded
        if scored > conceded:
            self.points += WIN
        elif scored == conceded:
            self.points += DRAW


def group_fixtures(teams: list[str]) -> list[tuple[str, str]]:
    """Single round-robin: every pair plays once (group-stage style)."""
    return list(combinations(teams, 2))


def group_matchdays(teams: list[str]) -> list[list[tuple[str, str]]]:
    """FIFA 4-team matchday schedule. The final matchday's two games involve
    disjoint pairs played simultaneously -- the simultaneity FIFA introduced
    after Gijon. (Cross-group best-third dependencies are *not* covered by it.)"""
    t0, t1, t2, t3 = teams
    return [
        [(t0, t1), (t2, t3)],   # MD1
        [(t0, t2), (t3, t1)],   # MD2
        [(t3, t0), (t1, t2)],   # MD3 (final, simultaneous)
    ]


def _records(teams: list[str], results: list[MatchResult]) -> dict[str, TeamRecord]:
    rec = {t: TeamRecord(t) for t in teams}
    for m in results:
        rec[m.home].add(m.hg, m.ag)
        rec[m.away].add(m.ag, m.hg)
    return rec


def _head_to_head(tied: list[str], results: list[MatchResult]) -> list[str]:
    """Rank ``tied`` teams by results among themselves (points, GD, GF)."""
    sub = [m for m in results if m.home in tied and m.away in tied]
    rec = _records(tied, sub)
    return sorted(tied, key=lambda t: (rec[t].points, rec[t].gd, rec[t].gf), reverse=True)


def rank_group(teams: list[str], results: list[MatchResult],
               rng=None) -> list[TeamRecord]:
    """Return group records ranked by FIFA criteria (best first)."""
    rec = _records(teams, results)
    # primary sort: points, GD, GF
    ordered = sorted(teams, key=lambda t: (rec[t].points, rec[t].gd, rec[t].gf), reverse=True)
    # refine exact ties (equal on points, GD, GF) via head-to-head, then RNG
    out: list[str] = []
    i = 0
    while i < len(ordered):
        j = i
        key_i = (rec[ordered[i]].points, rec[ordered[i]].gd, rec[ordered[i]].gf)
        while j + 1 < len(ordered) and (
            rec[ordered[j + 1]].points, rec[ordered[j + 1]].gd, rec[ordered[j + 1]].gf
        ) == key_i:
            j += 1
        block = ordered[i:j + 1]
        if len(block) > 1:
            block = _head_to_head(block, results)
            if rng is not None and len(block) > 1:
                # final tiebreak (drawing of lots) — seeded, only perturbs genuine ties
                rng.shuffle(block)
        out.extend(block)
        i = j + 1
    return [rec[t] for t in out]


def best_third_placed(thirds: list[TeamRecord], n: int = 8) -> list[str]:
    """Select the ``n`` best third-placed teams across groups (48-team rule).

    Ranking key mirrors FIFA: points, GD, goals scored. The *identity* of which
    groups they come from is exactly the cross-group dependency that makes the
    48-team final matchday manipulable (THEORY.md sec. 2).
    """
    ranked = sorted(thirds, key=lambda r: (r.points, r.gd, r.gf), reverse=True)
    return [r.team for r in ranked[:n]]


@dataclass
class FormatSpec:
    name: str
    n_teams: int
    n_groups: int
    group_size: int
    advance_top: int           # automatic qualifiers per group
    best_thirds: int = 0       # extra wildcard qualifiers (48-team: 8)

    @property
    def n_qualifiers(self) -> int:
        return self.n_groups * self.advance_top + self.best_thirds


SPEC_32 = FormatSpec("WC1998-2022", 32, 8, 4, advance_top=2, best_thirds=0)
SPEC_48 = FormatSpec("WC2026", 48, 12, 4, advance_top=2, best_thirds=8)


def assign_groups(teams_by_seed: list[str], spec: FormatSpec) -> list[list[str]]:
    """Snake-draft teams (already in seed order) into balanced groups.

    A reproducible stand-in for the official draw: pot-balanced and deterministic.
    Replace with the official 2026 draw for the pre-registration freeze.
    """
    groups: list[list[str]] = [[] for _ in range(spec.n_groups)]
    for pot in range(spec.group_size):
        row = teams_by_seed[pot * spec.n_groups:(pot + 1) * spec.n_groups]
        if pot % 2 == 1:
            row = list(reversed(row))
        for g, team in enumerate(row):
            groups[g].append(team)
    return groups
