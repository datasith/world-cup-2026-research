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
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make repo root importable

from src.wc2026 import data, fit_elo
from src.wc2026.engine import SimEngine, DecisionState
from src.wc2026.formats import SPEC_32, SPEC_48, assign_groups, group_matchdays
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
    """Return per-state (manipulable, cross_group) boolean arrays for the format."""
    rng = np.random.default_rng(seed)
    groups = assign_groups(field, spec)
    manip, cross = [], []
    for _ in range(n_snapshots):
        fixed = md12_snapshot(groups, sampler, rng)
        eng = SimEngine(groups, spec, sampler, strength_rank,
                        n_inner=n_inner, seed=int(rng.integers(1 << 30)))
        for gi, teams in enumerate(groups):
            md3 = group_matchdays(teams)[2]
            for team in teams:
                state = DecisionState(fixed=fixed, group_index=gi, team=team, md3=md3)
                r = eng.assess(team, state, min_delta=min_delta)
                manip.append(r.manipulable)
                cross.append(r.cross_group and r.manipulable)
    return np.array(manip, dtype=float), np.array(cross, dtype=float)


def bootstrap_ci(x, stat=np.mean, n_boot=2000, alpha=0.05, rng=None):
    rng = rng or np.random.default_rng(0)
    n = len(x)
    boots = [stat(x[rng.integers(0, n, n)]) for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return stat(x), lo, hi


def ratio_ci(num, den, n_boot=2000, alpha=0.05, rng=None):
    """Bootstrap CI for rho(num)/rho(den) (manipulability-rate ratio)."""
    rng = rng or np.random.default_rng(1)
    nn, nd = len(num), len(den)
    boots = []
    for _ in range(n_boot):
        rn = num[rng.integers(0, nn, nn)].mean()
        rd = den[rng.integers(0, nd, nd)].mean()
        boots.append(rn / rd if rd > 0 else np.inf)
    point = num.mean() / den.mean() if den.mean() > 0 else np.inf
    lo, hi = np.percentile([b for b in boots if np.isfinite(b)], [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return point, lo, hi


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
    m32, c32 = evaluate_format(SPEC_32, f32, r32, sampler, args.snapshots, args.inner,
                               args.margin, args.seed)

    print("[3/3] evaluating 48-team format ...")
    f48, r48 = build_field(model, 48)
    m48, c48 = evaluate_format(SPEC_48, f48, r48, sampler, args.snapshots, args.inner,
                               args.margin, args.seed + 1)

    boot = np.random.default_rng(args.seed + 99)
    print("\n=== manipulability (final-matchday decisions; 95% bootstrap CIs) ===")
    print(f"snapshots={args.snapshots} inner={args.inner} margin={args.margin}")
    for label, m, c in (("32-team", m32, c32), ("48-team", m48, c48)):
        rho, rlo, rhi = bootstrap_ci(m, rng=boot)
        # cross-group share = P(cross-group | manipulable)
        cg = c.sum() / m.sum() if m.sum() > 0 else 0.0
        print(f"  {label}: rho={rho:.3f} [{rlo:.3f}, {rhi:.3f}]  "
              f"cross_group_share={cg:.3f}  n_states={len(m)}  n_manip={int(m.sum())}")
    pt, lo, hi = ratio_ci(m48, m32, rng=boot)
    print(f"  EXPANSION MULTIPLIER rho(48)/rho(32) = {pt:.2f} [{lo:.2f}, {hi:.2f}]")


if __name__ == "__main__":
    main()
