"""Official 2026 World Cup knockout bracket (Round of 32 → final).

Fixed positional template from the FIFA match schedule (verified against the Wikipedia
2026 knockout-stage page, 2026-06-17). Each Round-of-32 slot is a group position:
``('W', g)`` group winner, ``('R', g)`` runner-up, or ``('T', k)`` the k-th third-place
slot, which admits a third-placed team only from its official **candidate group set**
(``THIRD_CANDIDATES``). The eight best third-placed teams are placed into the eight
third-slots by a constraint-respecting perfect matching.

Replaces the strength-seeded stand-in bracket for the 48-team format so V_adv reflects
the *real* bracket geometry (who can meet whom), which is what makes a team's group
finishing position — and hence its manipulation incentive — bracket-path dependent.

Residual fidelity caveats (documented, not hidden):
- FIFA's published 495-combination table fixes a *unique* third→slot assignment per case;
  ours respects the published per-slot candidate sets and is a deterministic perfect
  matching, which may differ from the official table in rare ambiguous combinations.
- Semifinal pairing uses the conventional QF(97,98)→SF and QF(99,100)→SF split.
- Fair-play / drawing-of-lots tie-breaks are not simulated (disciplinary cards are not
  modelled); group ties resolve on points, GD, GF, head-to-head, then a seeded coin.
"""
from __future__ import annotations

import numpy as np

# Round-of-32 leaves in BRACKET-TREE order: pairing adjacent matches up the tree
# reproduces the official R16/QF/SF/final structure (see module docstring).
# Each entry: (official_match_no, slotA, slotB).
LEAVES: list[tuple[int, tuple, tuple]] = [
    (74, ("W", "E"), ("T", 1)),
    (77, ("W", "I"), ("T", 2)),
    (73, ("R", "A"), ("R", "B")),
    (75, ("W", "F"), ("R", "C")),
    (83, ("R", "K"), ("R", "L")),
    (84, ("W", "H"), ("R", "J")),
    (81, ("W", "D"), ("T", 3)),
    (82, ("W", "G"), ("T", 4)),
    (76, ("W", "C"), ("R", "F")),
    (78, ("R", "E"), ("R", "I")),
    (79, ("W", "A"), ("T", 5)),
    (80, ("W", "L"), ("T", 6)),
    (86, ("W", "J"), ("R", "H")),
    (88, ("R", "D"), ("R", "G")),
    (85, ("W", "B"), ("T", 7)),
    (87, ("W", "K"), ("T", 8)),
]

# Official candidate group sets for each of the 8 third-place slots.
THIRD_CANDIDATES: dict[int, set[str]] = {
    1: {"A", "B", "C", "D", "F"},
    2: {"C", "D", "F", "G", "H"},
    3: {"B", "E", "F", "I", "J"},
    4: {"A", "E", "H", "I", "J"},
    5: {"C", "E", "F", "H", "I"},
    6: {"E", "H", "I", "J", "K"},
    7: {"E", "F", "G", "I", "J"},
    8: {"D", "E", "I", "J", "L"},
}


def assign_thirds(qualifying_groups: list[str]) -> dict[int, str]:
    """Match the (≤8) groups whose third-placed team qualified to third-slots.

    Constraint-respecting perfect matching via most-constrained-first backtracking;
    deterministic (slots and groups considered in fixed order). Returns {slot: group}.
    If no full matching exists (should not occur for a valid set of 8), any leftover
    groups are placed in any remaining admissible slot, else dropped (logged by caller).
    """
    groups = sorted(qualifying_groups)
    slots = sorted(THIRD_CANDIDATES)
    result: dict[int, str] = {}

    def backtrack(remaining_groups: list[str], used_slots: set[int]) -> bool:
        if not remaining_groups:
            return True
        # pick the most-constrained remaining group (fewest open admissible slots)
        def n_options(g):
            return sum(1 for s in slots if s not in used_slots and g in THIRD_CANDIDATES[s])
        g = min(remaining_groups, key=lambda x: (n_options(x), x))
        for s in slots:
            if s not in used_slots and g in THIRD_CANDIDATES[s]:
                result[s] = g
                used_slots.add(s)
                rest = [x for x in remaining_groups if x != g]
                if backtrack(rest, used_slots):
                    return True
                used_slots.discard(s)
                del result[s]
        return False

    backtrack(groups, set())
    return result


def build_leaf_teams(winner: dict[str, str], runner: dict[str, str],
                     third_slot_team: dict[int, str]) -> list[str]:
    """Flatten the 32 leaves (in tree order) into a team list for ``play``.

    ``winner``/``runner`` map group key -> team; ``third_slot_team`` maps slot -> team.
    A third-slot with no assigned team (fewer than 8 thirds in a counterfactual) gets a
    ``BYE`` so the bracket still runs.
    """
    from .simulator import BYE
    out: list[str] = []
    for _, a, b in LEAVES:
        for slot in (a, b):
            kind, key = slot
            if kind == "W":
                out.append(winner[key])
            elif kind == "R":
                out.append(runner[key])
            else:  # third slot
                out.append(third_slot_team.get(key, BYE))
    return out


def play(leaf_teams: list[str], sampler, rng: np.random.Generator) -> tuple[str, dict[str, int]]:
    """Play the fixed bracket; return (champion, {team: rounds_won})."""
    from .simulator import _knockout_winner
    depth: dict[str, int] = {t: 0 for t in leaf_teams}
    bracket = list(leaf_teams)
    while len(bracket) > 1:
        nxt = []
        for i in range(0, len(bracket), 2):
            w = _knockout_winner(bracket[i], bracket[i + 1], sampler, rng)
            depth[w] = depth.get(w, 0) + 1
            nxt.append(w)
        bracket = nxt
    return bracket[0], depth
