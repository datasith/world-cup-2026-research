"""First manipulability run: contrast 32- vs 48-team formats on real strengths.

Pipeline:
  1. Fit Elo on history; take the top-N teams as a plausible field (stand-in for
     the official draw -- to be replaced by the real 2026 draw at freeze time).
  2. Snake-draft into groups; simulate MD1-2 to make a pre-final-matchday state.
  3. For every team's final-matchday decision, test manipulability via SimEngine.
  4. Report manipulability rate rho, cross-group share, and the expansion
     multiplier rho(48)/rho(32), averaged over several MD1-2 snapshots.

Usage:
  uv run python scripts/run_manipulability.py --snapshots 5 --inner 80 --sims-margin 0.05
"""
from __future__ import annotations

import argparse

import numpy as np

from src.wc2026 import data, fit_elo
from src.wc2026.engine import SimEngine, DecisionState
from src.wc2026.formats import SPEC_32, SPEC_48, assign_groups, group_matchdays
from src.wc2026.manipulability import is_manipulable, summarize, expansion_multiplier
from src.wc2026.samplers import EloSampler


def build_field(model, n):
    ranked = [t for t, _ in sorted(model.ratings.items(), key=lambda kv: kv[1], reverse=True)]
    field = ranked[:n]
    strength_rank = {t: i for i, t in enumerate(field)}
    return field, strength_rank


def md12_snapshot(groups, sampler, rng):
    """Simulate matchdays 1-2 of every group; return fixed-results dict."""
    fixed = {}
    for teams in groups:
        for pairs in group_matchdays(teams)[:2]:   # MD1, MD2
            for h, a in pairs:
                fixed[(h, a)] = sampler.sample(h, a, neutral=True, rng=rng)
    return fixed


def evaluate_format(spec, field, strength_rank, sampler, n_snapshots, n_inner,
                    min_delta, seed):
    rng = np.random.default_rng(seed)
    groups = assign_groups(field, spec)
    results = []
    for _ in range(n_snapshots):
        fixed = md12_snapshot(groups, sampler, rng)
        eng = SimEngine(groups, spec, sampler, strength_rank,
                        n_inner=n_inner, seed=int(rng.integers(1 << 30)))
        for gi, teams in enumerate(groups):
            md3 = group_matchdays(teams)[2]
            for team in teams:
                state = DecisionState(fixed=fixed, group_index=gi, team=team, md3=md3)
                results.append(is_manipulable(eng, team, state, min_delta=min_delta))
    return summarize(results)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", type=int, default=3)
    ap.add_argument("--inner", type=int, default=60)
    ap.add_argument("--margin", type=float, default=0.05, help="noise margin on delta")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    print("[1/3] fitting Elo on history ...")
    df = data.load_results()
    model, _ = fit_elo.fit(df)
    sampler = EloSampler(model)

    print("[2/3] evaluating 32-team format ...")
    f32, r32 = build_field(model, 32)
    s32 = evaluate_format(SPEC_32, f32, r32, sampler, args.snapshots, args.inner,
                          args.margin, args.seed)

    print("[3/3] evaluating 48-team format ...")
    f48, r48 = build_field(model, 48)
    s48 = evaluate_format(SPEC_48, f48, r48, sampler, args.snapshots, args.inner,
                          args.margin, args.seed + 1)

    print("\n=== manipulability (final-matchday decisions) ===")
    print(f"snapshots={args.snapshots} inner={args.inner} margin={args.margin}")
    for label, s in (("32-team", s32), ("48-team", s48)):
        print(f"  {label}: rho={s.rho:.3f}  delta_bar={s.delta_bar:.3f}  "
              f"cross_group_share={s.cross_group_share:.3f}  n_states={s.n_states}")
    print(f"  EXPANSION MULTIPLIER rho(48)/rho(32) = {expansion_multiplier(s48, s32):.2f}")


if __name__ == "__main__":
    main()
