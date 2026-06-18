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
                    min_delta, seed, groups=None, objective="depth"):
    """Return per-state (manipulable, cross_group, snapshot_id) arrays for the format.

    ``snapshot_id`` records which Monte-Carlo snapshot each state came from. States
    within a snapshot share the same simulated MD1-2 results and are therefore
    correlated -- the bootstrap must resample *snapshots* (clusters), not individual
    states, to avoid understating the CIs.

    ``groups`` lets the caller pass the official draw; otherwise teams are
    snake-drafted from ``field`` (matched-strength baseline)."""
    rng = np.random.default_rng(seed)
    if groups is None:
        groups = assign_groups(field, spec)
    manip, cross, snap = [], [], []
    for s in range(n_snapshots):
        fixed = md12_snapshot(groups, sampler, rng)
        eng = SimEngine(groups, spec, sampler, strength_rank,
                        n_inner=n_inner, seed=int(rng.integers(1 << 30)), objective=objective)
        for gi, teams in enumerate(groups):
            md3 = group_matchdays(teams)[2]
            for team in teams:
                state = DecisionState(fixed=fixed, group_index=gi, team=team, md3=md3)
                r = eng.assess(team, state, min_delta=min_delta)
                manip.append(r.manipulable)
                cross.append(r.cross_group and r.manipulable)
                snap.append(s)
    return (np.array(manip, dtype=float), np.array(cross, dtype=float),
            np.array(snap, dtype=int))


def _by_cluster(x, snap):
    """Group values by snapshot id -> list of per-snapshot arrays (the resample units)."""
    return [x[snap == s] for s in np.unique(snap)]


def bootstrap_ci(x, snap, stat=np.mean, n_boot=2000, alpha=0.05, rng=None):
    """Cluster bootstrap: resample whole snapshots (clusters), then pool their states.

    Propagates the between-snapshot variance (the dominant source), which the naive
    per-state bootstrap ignored.
    """
    rng = rng or np.random.default_rng(0)
    clusters = _by_cluster(x, snap)
    k = len(clusters)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, k, k)
        pooled = np.concatenate([clusters[i] for i in idx])
        boots.append(stat(pooled))
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return stat(x), lo, hi


def ratio_ci(num, snum, den, sden, n_boot=2000, alpha=0.05, rng=None):
    """Cluster-bootstrap CI for rho(num)/rho(den) (manipulability-rate ratio).

    Resamples snapshots within each (independent) format arm.
    """
    rng = rng or np.random.default_rng(1)
    cn, cd = _by_cluster(num, snum), _by_cluster(den, sden)
    kn, kd = len(cn), len(cd)
    boots = []
    for _ in range(n_boot):
        rn = np.concatenate([cn[i] for i in rng.integers(0, kn, kn)]).mean()
        rd = np.concatenate([cd[i] for i in rng.integers(0, kd, kd)]).mean()
        boots.append(rn / rd if rd > 0 else np.inf)
    point = num.mean() / den.mean() if den.mean() > 0 else np.inf
    finite = [b for b in boots if np.isfinite(b)]
    if not finite:                       # denominator rate ~0 in every resample
        return point, float("nan"), float("nan")
    lo, hi = np.percentile(finite, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return point, lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", type=int, default=3)
    ap.add_argument("--inner", type=int, default=60)
    ap.add_argument("--margin", type=float, default=0.05, help="noise margin on delta")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--official", action="store_true",
                    help="use the official 2026 draw for the 48-team arm")
    ap.add_argument("--objective", choices=["depth", "qualify", "champion"], default="depth",
                    help="V_adv functional: knockout rounds won / P(qualify) / P(champion)")
    args = ap.parse_args()

    print("[1/3] fitting Elo on history ...")
    df = data.load_results()
    model, _ = fit_elo.fit(df)
    sampler = EloSampler(model)

    official_groups = None
    if args.official:
        draw = data.load_draw()
        official_groups = draw["groups"]
        field48 = [t for g in official_groups for t in g]
        r48 = {t: i for i, t in enumerate(sorted(field48, key=model.rating, reverse=True))}
        print(f"    using OFFICIAL 2026 draw ({len(field48)} teams)")
    else:
        field48, r48 = build_field(model, 48)

    print("[2/3] evaluating 32-team format ...")
    f32, r32 = build_field(model, 32)
    m32, c32, s32 = evaluate_format(SPEC_32, f32, r32, sampler, args.snapshots, args.inner,
                                    args.margin, args.seed, objective=args.objective)

    print("[3/3] evaluating 48-team format ...")
    m48, c48, s48 = evaluate_format(SPEC_48, field48, r48, sampler, args.snapshots, args.inner,
                                    args.margin, args.seed + 1, groups=official_groups,
                                    objective=args.objective)

    boot = np.random.default_rng(args.seed + 99)
    print("\n=== manipulability (final-matchday decisions; 95% cluster-bootstrap CIs) ===")
    print(f"snapshots={args.snapshots} inner={args.inner} margin={args.margin} "
          f"objective={args.objective} (CIs resample whole snapshots)")
    for label, m, c, s in (("32-team", m32, c32, s32), ("48-team", m48, c48, s48)):
        rho, rlo, rhi = bootstrap_ci(m, s, rng=boot)
        # cross-group share = P(cross-group | manipulable)
        cg = c.sum() / m.sum() if m.sum() > 0 else 0.0
        print(f"  {label}: rho={rho:.3f} [{rlo:.3f}, {rhi:.3f}]  "
              f"cross_group_share={cg:.3f}  n_states={len(m)}  n_manip={int(m.sum())}")
    pt, lo, hi = ratio_ci(m48, s48, m32, s32, rng=boot)
    print(f"  EXPANSION MULTIPLIER rho(48)/rho(32) = {pt:.2f} [{lo:.2f}, {hi:.2f}]")


if __name__ == "__main__":
    main()
