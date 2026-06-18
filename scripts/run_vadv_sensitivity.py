"""V_adv specification sensitivity for the expansion multiplier (reviewer C1).

R1 flagged that V_adv (advancement value) was under-specified and asked us to show the
headline conclusions are invariant to defensible alternative specifications. We re-run the
32-vs-48 multiplier under three V_adv functionals, all estimated from the same
sub-simulations (engine objective):

  depth     -- expected knockout rounds won (canonical; 0 if eliminated -> subsumes both
               "probability of advancing" and "bracket-path strength")
  qualify   -- probability of advancing past the group stage (pure tanking-to-qualify)
  champion  -- probability of winning the title (win-probability-weighted to the end)

Reports rho(32), rho(48), cross-group share, and the multiplier with cluster CIs under each.

Usage:
  uv run python scripts/run_vadv_sensitivity.py --official --snapshots 160 --inner 150
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wc2026 import data, fit_elo
from src.wc2026.formats import SPEC_32, SPEC_48
from src.wc2026.samplers import EloSampler
from scripts.run_manipulability import build_field, evaluate_format, bootstrap_ci, ratio_ci


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", type=int, default=160)
    ap.add_argument("--inner", type=int, default=150)
    ap.add_argument("--margin", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--official", action="store_true")
    ap.add_argument("--objectives", nargs="*", default=["depth", "qualify", "champion"])
    ap.add_argument("--out", type=str, default="results/vadv_sensitivity.json")
    args = ap.parse_args()

    print("[setup] fitting Elo + field/draw ...")
    df = data.load_results()
    model, _ = fit_elo.fit(df)
    sampler = EloSampler(model)
    official_groups = data.load_draw()["groups"] if args.official else None
    if args.official:
        field48 = [t for g in official_groups for t in g]
        r48 = {t: i for i, t in enumerate(sorted(field48, key=model.rating, reverse=True))}
    else:
        field48, r48 = build_field(model, 48)
    f32, r32 = build_field(model, 32)

    rows = []
    for obj in args.objectives:
        print(f"[obj={obj}] evaluating 32 then 48 ({args.snapshots}x{args.inner}) ...")
        m32, c32, s32 = evaluate_format(SPEC_32, f32, r32, sampler, args.snapshots,
                                        args.inner, args.margin, args.seed, objective=obj)
        m48, c48, s48 = evaluate_format(SPEC_48, field48, r48, sampler, args.snapshots,
                                        args.inner, args.margin, args.seed + 1,
                                        groups=official_groups, objective=obj)
        boot = np.random.default_rng(args.seed + 99)
        r32v, lo32, hi32 = bootstrap_ci(m32, s32, rng=boot)
        r48v, lo48, hi48 = bootstrap_ci(m48, s48, rng=boot)
        mult, mlo, mhi = ratio_ci(m48, s48, m32, s32, rng=boot)
        cg48 = c48.sum() / m48.sum() if m48.sum() > 0 else 0.0
        rows.append({"objective": obj,
                     "rho32": r32v, "rho32_ci": [lo32, hi32],
                     "rho48": r48v, "rho48_ci": [lo48, hi48],
                     "cross_group_share_48": cg48,
                     "multiplier": mult, "multiplier_ci": [mlo, mhi],
                     "n_manip32": int(m32.sum()), "n_manip48": int(m48.sum())})

    out = {"meta": {"snapshots": args.snapshots, "inner": args.inner, "margin": args.margin,
                    "seed": args.seed, "official": args.official}, "by_objective": rows}
    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(json.dumps(out, indent=2))

    print(f"\n=== V_adv sensitivity (snapshots={args.snapshots} inner={args.inner} "
          f"{'official' if args.official else 'synthetic'} draw) ===")
    print(f"{'objective':>10} {'rho32':>7} {'rho48':>7} {'xgroup48':>9} {'multiplier':>12} {'95% CI':>16}")
    for r in rows:
        lo, hi = r["multiplier_ci"]
        ci = f"[{lo:.2f}, {hi:.2f}]" if np.isfinite(lo) else "[n/a]"
        print(f"{r['objective']:>10} {r['rho32']:>7.3f} {r['rho48']:>7.3f} "
              f"{r['cross_group_share_48']:>9.3f} {r['multiplier']:>12.2f} {ci:>16}")
    print(f"\ndata -> {outpath}")


if __name__ == "__main__":
    main()
