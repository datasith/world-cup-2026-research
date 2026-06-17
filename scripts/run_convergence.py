"""Monte-Carlo convergence diagnostic for the expansion multiplier (reviewer R3).

R3 asked us to show the cluster-bootstrap CIs have converged: plot the multiplier (and
its 95% CI) as a function of the number of snapshots. We run the full evaluation **once**
at the maximum snapshot count, then -- because snapshots are i.i.d. -- compute the point
estimate and cluster CI on increasing *prefixes* of the snapshots. That yields the whole
convergence curve from a single pass per format arm.

Outputs results/convergence.json and results/convergence.png.

Usage:
  uv run python scripts/run_convergence.py --official --max-snapshots 400 --inner 150
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
    ap.add_argument("--max-snapshots", type=int, default=400)
    ap.add_argument("--inner", type=int, default=150)
    ap.add_argument("--margin", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--official", action="store_true",
                    help="use the official 2026 draw for the 48-team arm")
    ap.add_argument("--grid", type=int, nargs="*",
                    default=[10, 20, 40, 80, 120, 160, 240, 320, 400])
    ap.add_argument("--out", type=str, default="results/convergence.json")
    args = ap.parse_args()

    grid = sorted(k for k in args.grid if k <= args.max_snapshots)
    if grid[-1] != args.max_snapshots:
        grid.append(args.max_snapshots)

    print("[1/3] fitting Elo ...")
    df = data.load_results()
    model, _ = fit_elo.fit(df)
    sampler = EloSampler(model)

    official_groups = None
    if args.official:
        official_groups = data.load_draw()["groups"]
        field48 = [t for g in official_groups for t in g]
        r48 = {t: i for i, t in enumerate(sorted(field48, key=model.rating, reverse=True))}
    else:
        field48, r48 = build_field(model, 48)
    f32, r32 = build_field(model, 32)

    print(f"[2/3] evaluating both formats at {args.max_snapshots} snapshots ...")
    m32, _, s32 = evaluate_format(SPEC_32, f32, r32, sampler, args.max_snapshots,
                                  args.inner, args.margin, args.seed)
    m48, _, s48 = evaluate_format(SPEC_48, field48, r48, sampler, args.max_snapshots,
                                  args.inner, args.margin, args.seed + 1, groups=official_groups)

    print("[3/3] computing convergence curve over snapshot prefixes ...")
    boot = np.random.default_rng(args.seed + 99)
    rows = []
    for k in grid:
        a32, sa32 = m32[s32 < k], s32[s32 < k]
        a48, sa48 = m48[s48 < k], s48[s48 < k]
        r32k, lo32, hi32 = bootstrap_ci(a32, sa32, rng=boot)
        r48k, lo48, hi48 = bootstrap_ci(a48, sa48, rng=boot)
        mult, mlo, mhi = ratio_ci(a48, sa48, a32, sa32, rng=boot)
        rows.append({"snapshots": k,
                     "rho32": r32k, "rho32_ci": [lo32, hi32],
                     "rho48": r48k, "rho48_ci": [lo48, hi48],
                     "multiplier": mult, "multiplier_ci": [mlo, mhi],
                     "ci_width": mhi - mlo})

    out = {"meta": {"max_snapshots": args.max_snapshots, "inner": args.inner,
                    "margin": args.margin, "seed": args.seed,
                    "official": args.official, "grid": grid},
           "curve": rows}
    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(json.dumps(out, indent=2))

    # report
    print(f"\n=== expansion-multiplier convergence ({'official' if args.official else 'synthetic'} "
          f"draw, inner={args.inner}) ===")
    print(f"{'snaps':>6} {'mult':>6} {'95% CI':>16} {'CI width':>9}")
    for r in rows:
        lo, hi = r["multiplier_ci"]
        print(f"{r['snapshots']:>6} {r['multiplier']:>6.2f}  [{lo:>5.2f}, {hi:>5.2f}]   {r['ci_width']:>7.3f}")

    # plot
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ks = [r["snapshots"] for r in rows]
        mult = [r["multiplier"] for r in rows]
        lo = [r["multiplier_ci"][0] for r in rows]
        hi = [r["multiplier_ci"][1] for r in rows]
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.fill_between(ks, lo, hi, alpha=0.2, color="C0", label="95% cluster-bootstrap CI")
        ax.plot(ks, mult, "o-", color="C0", label="multiplier ρ(48)/ρ(32)")
        ax.axhline(1.0, ls="--", color="grey", lw=1, label="no effect (=1)")
        ax.set_xlabel("number of snapshots (outer Monte-Carlo)")
        ax.set_ylabel("expansion multiplier")
        ax.set_title(f"Multiplier convergence vs snapshot budget (inner={args.inner})")
        ax.legend(); fig.tight_layout()
        png = outpath.with_suffix(".png")
        fig.savefig(png, dpi=130)
        print(f"\nplot  -> {png}")
    except Exception as e:  # noqa: BLE001 - plotting is optional
        print(f"\n(plot skipped: {e})")
    print(f"data  -> {outpath}")


if __name__ == "__main__":
    main()
