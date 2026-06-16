"""Monte Carlo tournament simulator (32- vs 48-team formats).

Given a MatchSampler (Elo or Poisson) and a group assignment, simulate the full
tournament many times and aggregate champion / round-reach distributions. The
same machinery, driven from a *partial* state, powers the manipulability engine
(engine.py): it lets us value a team's target result by conditioning its current
match and simulating the remainder.

Knockout matches are played at neutral venues and cannot draw (penalties are
modelled as a coin-flip weighted by the win-expectancy split of the sampler).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from .formats import (
    FormatSpec,
    MatchResult,
    best_third_placed,
    group_fixtures,
    rank_group,
)
from .samplers import MatchSampler


@dataclass
class GroupOutcome:
    ranked: list                      # list[TeamRecord], best first
    results: list[MatchResult]


def play_group(teams: list[str], sampler: MatchSampler, rng: np.random.Generator,
               fixed: dict[tuple[str, str], tuple[int, int]] | None = None) -> GroupOutcome:
    """Simulate one group. ``fixed`` injects already-known/forced scorelines."""
    results = []
    for h, a in group_fixtures(teams):
        if fixed and (h, a) in fixed:
            hg, ag = fixed[(h, a)]
        else:
            hg, ag = sampler.sample(h, a, neutral=True, rng=rng)
        results.append(MatchResult(h, a, hg, ag))
    return GroupOutcome(rank_group(teams, results, rng=rng), results)


def _knockout_winner(a: str, b: str, sampler: MatchSampler,
                     rng: np.random.Generator) -> str:
    """Single elimination match; ties broken by a strength-weighted shootout."""
    hg, ag = sampler.sample(a, b, neutral=True, rng=rng)
    if hg > ag:
        return a
    if ag > hg:
        return b
    la, lb = sampler.expected_goals(a, b, neutral=True)
    return a if rng.random() < la / (la + lb) else b


def _seed_bracket(qualifiers: list[str]) -> list[str]:
    """Order qualifiers into a standard 1-vs-N single-elimination bracket.

    ``qualifiers`` is assumed in overall seeding order (strongest first); the
    returned order pairs adjacent slots (0,1),(2,3),... so the top seed meets the
    bottom seed first and seeds 1 and 2 can only meet in the final. ``len`` must
    be a power of two (32 and 16 qualifiers both are). The official cross-group
    R32 pairing table can replace this for the freeze.
    """
    n = len(qualifiers)
    seeds = [0]
    while len(seeds) < n:
        m = len(seeds) * 2
        seeds = [s for pair in ((x, m - 1 - x) for x in seeds) for s in pair]
    return [qualifiers[i] for i in seeds]


def play_knockout(qualifiers_seeded: list[str], sampler: MatchSampler,
                  rng: np.random.Generator) -> list[str]:
    """Run single elimination from a seeded qualifier list; return [champion, ...rounds]."""
    bracket = _seed_bracket(qualifiers_seeded)
    rounds_reached: list[str] = []
    while len(bracket) > 1:
        nxt = []
        for i in range(0, len(bracket), 2):
            nxt.append(_knockout_winner(bracket[i], bracket[i + 1], sampler, rng))
        bracket = nxt
        rounds_reached.append(bracket[0])  # placeholder progression marker
    return bracket  # [champion]


def qualifiers(groups_outcomes: list[GroupOutcome], spec: FormatSpec,
               strength_rank: dict[str, int]) -> list[str]:
    """Collect qualifiers per the format and return them in overall seed order."""
    quals: list[str] = []
    thirds = []
    for go in groups_outcomes:
        for pos, rec in enumerate(go.ranked):
            if pos < spec.advance_top:
                quals.append(rec.team)
            elif pos == spec.advance_top and spec.best_thirds:
                thirds.append(rec)
    if spec.best_thirds:
        quals.extend(best_third_placed(thirds, spec.best_thirds))
    # seed by pre-tournament strength (lower rank index = stronger)
    return sorted(quals, key=lambda t: strength_rank.get(t, 10**9))


def simulate_tournament(groups: list[list[str]], spec: FormatSpec,
                        sampler: MatchSampler, strength_rank: dict[str, int],
                        rng: np.random.Generator) -> dict:
    """Simulate one full tournament; return champion and qualifier set."""
    outcomes = [play_group(g, sampler, rng) for g in groups]
    quals = qualifiers(outcomes, spec, strength_rank)
    champion = play_knockout(quals, sampler, rng)[0]
    return {"champion": champion, "qualifiers": quals, "groups": outcomes}


def run(groups: list[list[str]], spec: FormatSpec, sampler: MatchSampler,
        strength_rank: dict[str, int], n_sims: int = 10000,
        seed: int | None = None) -> dict:
    """Aggregate ``n_sims`` tournaments: champion probabilities and qualify rates."""
    rng = np.random.default_rng(seed)
    champs: Counter = Counter()
    qual_counts: Counter = Counter()
    for _ in range(n_sims):
        res = simulate_tournament(groups, spec, sampler, strength_rank, rng)
        champs[res["champion"]] += 1
        for t in res["qualifiers"]:
            qual_counts[t] += 1
    champ_p = {t: c / n_sims for t, c in champs.most_common()}
    qual_p = {t: c / n_sims for t, c in qual_counts.most_common()}
    return {"champion_probs": champ_p, "qualify_probs": qual_p, "n_sims": n_sims}
