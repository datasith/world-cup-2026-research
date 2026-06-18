"""Tests for the official 2026 knockout bracket (src/wc2026/bracket.py)."""
from __future__ import annotations

import numpy as np
import pytest

from src.wc2026 import bracket
from src.wc2026.simulator import BYE


def test_leaves_cover_all_positions_once():
    # 12 winners, 12 runners-up, 8 third-slots = 32 leaves
    winners, runners, thirds = set(), set(), set()
    for _, a, b in bracket.LEAVES:
        for kind, key in (a, b):
            (winners if kind == "W" else runners if kind == "R" else thirds).add(key)
    assert winners == set("ABCDEFGHIJKL")
    assert runners == set("ABCDEFGHIJKL")
    assert thirds == set(range(1, 9))
    assert sum(len(x) for x in (winners, runners, thirds)) == 32


def test_eight_winners_face_thirds():
    facing = {key for _, a, b in bracket.LEAVES for kind, key in (a, b)
              if kind == "W" and any(s[0] == "T" for s in (a, b))}
    assert facing == set("ABDEGIKL")          # official 8 winners paired with thirds


@pytest.mark.parametrize("groups", [
    list("ABCDEFGH"),                 # first eight
    list("EFGHIJKL"),                 # last eight
    list("ABEFIJKL"),                 # mixed, incl. K (only slot6) and L (only slot8)
    list("CDGHIJKL"),
])
def test_assign_thirds_is_valid_perfect_matching(groups):
    m = bracket.assign_thirds(groups)
    assert len(m) == len(groups)                       # every group placed
    assert len(set(m.keys())) == len(groups)           # distinct slots
    assert set(m.values()) == set(groups)              # exactly these groups
    for slot, g in m.items():
        assert g in bracket.THIRD_CANDIDATES[slot]     # respects candidate set


def test_kl_thirds_forced_to_their_unique_slots():
    m = bracket.assign_thirds(list("ABEFIJKL"))
    assert m[6] == "K"      # K appears only in slot 6
    assert m[8] == "L"      # L appears only in slot 8


def test_build_and_play_full_bracket_deterministic_winner_advances():
    winner = {g: f"W{g}" for g in "ABCDEFGHIJKL"}
    runner = {g: f"R{g}" for g in "ABCDEFGHIJKL"}
    third_groups = list("ABCDEFGH")
    slot_group = bracket.assign_thirds(third_groups)
    third_slot_team = {s: f"T{g}" for s, g in slot_group.items()}
    leaves = bracket.build_leaf_teams(winner, runner, third_slot_team)
    assert len(leaves) == 32
    assert BYE not in leaves                      # full field, no byes

    # deterministic sampler: 'home' always wins -> first leaf of each pair advances
    class FirstWins:
        def sample(self, a, b, neutral, rng):
            return (1, 0)
        def expected_goals(self, a, b, neutral=True):
            return (1.0, 1.0)

    champ, depth = bracket.play(leaves, FirstWins(), np.random.default_rng(0))
    assert champ == leaves[0]
    assert depth[champ] == 5                      # 32 -> 16 -> 8 -> 4 -> 2 -> 1 = 5 rounds
    assert depth[leaves[1]] == 0                  # lost round 1


def test_build_leaf_teams_pads_missing_thirds_with_bye():
    winner = {g: f"W{g}" for g in "ABCDEFGHIJKL"}
    runner = {g: f"R{g}" for g in "ABCDEFGHIJKL"}
    leaves = bracket.build_leaf_teams(winner, runner, {1: "TX"})   # only one third slot filled
    assert leaves.count(BYE) == 7                  # 8 third-slots, 1 filled -> 7 byes
