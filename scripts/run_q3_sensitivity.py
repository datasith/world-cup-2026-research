"""q3 / margin sensitivity sweep for the named MD3 predictions (PREREGISTRATION sec.4).

Shows the conclusions do not hinge on the manipulability margin. Runs the R4
projection ONCE per strength model, capturing each team's raw decision record
(adv_action, delta, q3_adv) per snapshot, then re-thresholds at margins
{0.03, 0.05, 0.08} *without* re-running the expensive sub-simulations. Reports,
per model: the named-match P(manipulable) at each margin, the cross-model-style
rank stability across margins (Spearman), and robust-set (P>=0.50) stability.

Usage:
  uv run python scripts/run_q3_sensitivity.py --snapshots 60 --inner 150 \
      --out results/q3_sensitivity.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wc2026 import data
from src.wc2026.engine import SimEngine, DecisionState
from src.wc2026.formats import SPEC_48, group_matchdays
from src.wc2026.manipulability import TargetResult
from scripts.run_r4_named import build_model, project_to_pre_md3, real_fixed

MARGINS = [0.03, 0.05, 0.08]
Q3_THRESHOLD = 0.05            # cross-group flag threshold (held fixed; prereg default)


def sweep_model(model_name, df, draw, args):
    """Return {margin: {match_key: {p_manip, p_cross}}} for one strength model."""
    sampler, strength_of, label = build_model(model_name, df, args.seed)
    groups = draw["groups"]
    group_keys = "ABCDEFGHIJKL"
    fixed_real = real_fixed(draw)
    strength_rank = {t: i for i, t in enumerate(
        sorted([t for g in groups for t in g], key=strength_of, reverse=True))}

    # per (margin) -> per (gk, match_pair) -> count of snapshots with a manip / cross team
    manip = {m: defaultdict(int) for m in MARGINS}
    cross = {m: defaultdict(int) for m in MARGINS}
    match_name = {}

    rng = np.random.default_rng(args.seed)
    for s in range(args.snapshots):
        fixed = project_to_pre_md3(groups, fixed_real, sampler, rng)
        eng = SimEngine(groups, SPEC_48, sampler, strength_rank,
                        n_inner=args.inner, seed=int(rng.integers(1 << 30)))
        for gi, teams in enumerate(groups):
            gk = group_keys[gi]
            md3 = group_matchdays(teams)[2]
            match_of = {t: frozenset(p) for p in md3 for t in p}
            # raw decision record per team (assess with margin=0 so nothing is pre-filtered)
            recs = {}
            for team in teams:
                r = eng.assess(team, DecisionState(fixed=fixed, group_index=gi,
                                                   team=team, md3=md3),
                               min_delta=0.0, q3_threshold=Q3_THRESHOLD)
                recs[team] = r
                mk = (gk, tuple(sorted(match_of[team])))
                match_name[mk] = f"{mk[1][0]} vs {mk[1][1]}"
            # re-threshold per margin, aggregate to match level
            for mg in MARGINS:
                man_match, cross_match = defaultdict(bool), defaultdict(bool)
                for team in teams:
                    r = recs[team]
                    is_manip = r.adv_action is not TargetResult.WIN and r.delta > mg
                    if is_manip:
                        mk = (gk, tuple(sorted(match_of[team])))
                        man_match[mk] = True
                        if r.q3_adv > Q3_THRESHOLD:
                            cross_match[mk] = True
                for mk, v in man_match.items():
                    if v:
                        manip[mg][mk] += 1
                        if cross_match[mk]:
                            cross[mg][mk] += 1
        if (s + 1) % 10 == 0:
            print(f"    [{model_name}] {s + 1}/{args.snapshots} snapshots")

    n = args.snapshots
    out = {}
    for mg in MARGINS:
        out[mg] = {mk: {"match": match_name[mk],
                        "p_manip": manip[mg][mk] / n,
                        "p_cross": cross[mg][mk] / n}
                   for mk in match_name}
    return label, out


def report(label, sweep):
    keys = sorted(sweep[MARGINS[0]])
    print(f"\n=== {label} ===")
    # rank stability across margins
    print("rank stability of P(manipulable) across margins (Spearman):")
    base = MARGINS[1]  # 0.05 reference
    for mg in MARGINS:
        if mg == base:
            continue
        a = [sweep[base][k]["p_manip"] for k in keys]
        b = [sweep[mg][k]["p_manip"] for k in keys]
        rho = spearmanr(a, b)[0]
        print(f"  margin {base:.2f} vs {mg:.2f}: rho = {rho:.3f}")
    # robust-set stability
    print("robust set (P_manip >= 0.50) size & stability:")
    sets = {mg: {k for k in keys if sweep[mg][k]["p_manip"] >= 0.50} for mg in MARGINS}
    ref = sets[base]
    for mg in MARGINS:
        s = sets[mg]
        jac = len(s & ref) / len(s | ref) if (s | ref) else 1.0
        print(f"  margin {mg:.2f}: |set| = {len(s):>2}  Jaccard vs 0.05 = {jac:.2f}")
    # per-match table for the union of robust sets
    union = sorted(set().union(*sets.values()),
                   key=lambda k: -sweep[base][k]["p_manip"])
    print(f"\n  {'Grp':>3} {'Match':<28} " + " ".join(f"m={m:.2f}" for m in MARGINS))
    for k in union:
        row = " ".join(f"{sweep[mg][k]['p_manip']:>5.0%}" for mg in MARGINS)
        print(f"  {k[0]:>3} {sweep[base][k]['match']:<28} {row}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", type=int, default=60)
    ap.add_argument("--inner", type=int, default=150)
    ap.add_argument("--seed", type=int, default=20260616)
    ap.add_argument("--out", type=str, default="results/q3_sensitivity.json")
    args = ap.parse_args()

    df = data.load_results()
    draw = data.load_draw()

    artifact = {"meta": {"snapshots": args.snapshots, "inner": args.inner,
                         "margins": MARGINS, "q3_threshold": Q3_THRESHOLD,
                         "seed": args.seed,
                         "conditioned_through": "2026-06-16 (16 MD1 results)"},
                "models": {}}
    for model_name in ("elo", "poisson"):
        print(f"[sweep] {model_name} ...")
        label, sweep = sweep_model(model_name, df, draw, args)
        report(label, sweep)
        artifact["models"][model_name] = {
            "label": label,
            "by_margin": {f"{mg:.2f}": {f"{k[0]}|{v['match']}": {"p_manip": v["p_manip"],
                                                                 "p_cross": v["p_cross"]}
                                        for k, v in sweep[mg].items()}
                          for mg in MARGINS},
        }

    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(json.dumps(artifact, ensure_ascii=False, indent=2))
    print(f"\nfull sweep -> {outpath}")


if __name__ == "__main__":
    main()
