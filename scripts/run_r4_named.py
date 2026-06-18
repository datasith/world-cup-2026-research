"""R4 -- named manipulable matches on the real 2026 field.

Conditions on the actual results played so far, projects each group forward to its
final matchday (MD3) over many Monte-Carlo continuations, and reports -- by name --
which MD3 matches contain a team whose advancement-optimal action is not to win,
how often, and whether the incentive is cross-group (best-third route).

This is the pre-registration artifact: run it before MD3 kicks off (~2026-06-24),
freeze the JSON, and score the named predictions against what the teams actually do.

Usage:
  uv run python scripts/run_r4_named.py --snapshots 50 --inner 150 --margin 0.05 \
      --out results/r4_named.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wc2026 import data, fit_elo
from src.wc2026.engine import SimEngine, DecisionState
from src.wc2026.formats import SPEC_48, group_matchdays
from src.wc2026.samplers import EloSampler, PoissonSampler


def build_model(name: str, df, seed: int):
    """Return (sampler, strength_fn) for the requested strength model.

    Both arms expose the same interface so the simulator is model-agnostic
    (THEORY.md sec. 4): Elo for the fast primary run, Bayesian Poisson for the
    pre-registered robustness check.
    """
    if name == "elo":
        model, _ = fit_elo.fit(df)
        return EloSampler(model), model.rating, "Elo (full-history)"
    if name == "poisson":
        from src.wc2026 import bayesian
        fit = bayesian.fit(data.training_window(df), seed=seed)
        return PoissonSampler(fit), fit.strength, "Bayesian Poisson (post-2018)"
    raise ValueError(f"unknown model: {name}")


def real_fixed(draw) -> dict:
    """(home, away) -> (hg, ag) for matches already played."""
    return {(r["home"], r["away"]): (r["hg"], r["ag"]) for r in draw["results"]}


def project_to_pre_md3(groups, fixed_real, sampler, rng) -> dict:
    """Build a pre-MD3 state: real MD1-2 where known, simulated otherwise."""
    fixed = {}
    for teams in groups:
        for pairs in group_matchdays(teams)[:2]:        # MD1, MD2
            for h, a in pairs:
                if (h, a) in fixed_real:
                    fixed[(h, a)] = fixed_real[(h, a)]
                elif (a, h) in fixed_real:
                    ag, hg = fixed_real[(a, h)]
                    fixed[(h, a)] = (hg, ag)
                else:
                    fixed[(h, a)] = sampler.sample(h, a, neutral=True, rng=rng)
    return fixed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", type=int, default=50)
    ap.add_argument("--inner", type=int, default=150)
    ap.add_argument("--margin", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20260616)
    ap.add_argument("--bracket", choices=["seeded", "official"], default="seeded",
                    help="knockout geometry: strength-seeded stand-in or the real 2026 bracket")
    ap.add_argument("--model", choices=["elo", "poisson"], default="elo",
                    help="strength model: elo (primary) or poisson (robustness)")
    ap.add_argument("--out", type=str, default="results/r4_named.json")
    args = ap.parse_args()

    print(f"[1/2] fitting {args.model} model + loading official draw ...")
    df = data.load_results()
    sampler, strength_of, model_label = build_model(args.model, df, args.seed)
    draw = data.load_draw()
    groups = draw["groups"]
    group_keys = "ABCDEFGHIJKL"
    fixed_real = real_fixed(draw)
    strength_rank = {t: i for i, t in enumerate(
        sorted([t for g in groups for t in g], key=strength_of, reverse=True))}

    # accumulators keyed by (group_key, frozenset(match teams)) and team
    match_manip = defaultdict(int)       # snapshots with >=1 manipulable team in the match
    match_cross = defaultdict(int)       # of those, how many were cross-group
    team_manip = defaultdict(int)
    team_cross = defaultdict(int)
    team_to_match = {}

    print(f"[2/2] projecting MD3 over {args.snapshots} snapshots x {args.inner} inner ...")
    rng = np.random.default_rng(args.seed)
    for s in range(args.snapshots):
        fixed = project_to_pre_md3(groups, fixed_real, sampler, rng)
        eng = SimEngine(groups, SPEC_48, sampler, strength_rank,
                        n_inner=args.inner, seed=int(rng.integers(1 << 30)),
                        bracket=args.bracket)
        for gi, teams in enumerate(groups):
            gk = group_keys[gi]
            md3 = group_matchdays(teams)[2]
            match_of = {t: frozenset(p) for p in md3 for t in p}
            manip_in_match = defaultdict(bool)
            cross_in_match = defaultdict(bool)
            for team in teams:
                r = eng.assess(team, DecisionState(fixed=fixed, group_index=gi,
                                                   team=team, md3=md3),
                               min_delta=args.margin)
                key_t = (gk, team)
                team_to_match[key_t] = (gk, tuple(sorted(match_of[team])))
                if r.manipulable:
                    team_manip[key_t] += 1
                    if r.cross_group:
                        team_cross[key_t] += 1
                    m = (gk, tuple(sorted(match_of[team])))
                    manip_in_match[m] = True
                    if r.cross_group:
                        cross_in_match[m] = True
            for m, val in manip_in_match.items():
                if val:
                    match_manip[m] += 1
                    if cross_in_match[m]:
                        match_cross[m] += 1
        if (s + 1) % 10 == 0:
            print(f"    {s + 1}/{args.snapshots} snapshots done")

    n = args.snapshots
    # build named match report
    matches = []
    for (gk, pair), cnt in match_manip.items():
        matches.append({
            "group": gk,
            "match": f"{pair[0]} vs {pair[1]}",
            "p_manipulable": cnt / n,
            "p_cross_group": match_cross[(gk, pair)] / n,
            "teams": pair,
        })
    matches.sort(key=lambda d: d["p_manipulable"], reverse=True)

    teams_report = []
    for (gk, team), cnt in team_manip.items():
        teams_report.append({
            "group": gk, "team": team,
            "p_manipulable": cnt / n,
            "p_cross_group": team_cross[(gk, team)] / n,
            "match": f"{team_to_match[(gk, team)][1][0]} vs {team_to_match[(gk, team)][1][1]}",
        })
    teams_report.sort(key=lambda d: d["p_manipulable"], reverse=True)

    out = {
        "meta": {
            "description": "R4 projected MD3 manipulability, conditioned on results to date",
            "conditioned_through": "2026-06-16 (16 of 24 MD1 matches played; rest simulated)",
            "snapshots": n, "inner": args.inner, "margin": args.margin,
            "strength_model": model_label, "seed": args.seed, "bracket": args.bracket,
        },
        "matches": matches,
        "teams": teams_report,
    }
    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print("\n=== R4: named manipulable MD3 matches (real 2026 field) ===")
    print(f"conditioned through {out['meta']['conditioned_through']}; "
          f"snapshots={n} inner={args.inner} margin={args.margin}\n")
    print(f"{'P(manip)':>9} {'P(cross)':>9}  Group  Match")
    for m in matches[:15]:
        print(f"{m['p_manipulable']:>8.0%} {m['p_cross_group']:>9.0%}   {m['group']:>4}   {m['match']}")
    print(f"\nfull report -> {outpath}")


if __name__ == "__main__":
    main()
