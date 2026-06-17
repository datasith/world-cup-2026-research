"""Factorial decomposition of the expansion multiplier (reviewer R1/R2 finding C3).

The headline multiplier rho(48)/rho(32) conflates several simultaneous changes: the
best-third wildcard rule, the field size (32->48), the group count (8->12), and the
draw. This isolates the **best-third rule** by holding the field, groups, and draw fixed
and toggling only the advancement rule:

  A) 48 / 12 groups / top-2 + 8 best-thirds   (the real 2026 format, official draw)
  B) 48 / 12 groups / top-2 ONLY              (same field/groups/draw; 24 qualifiers, byes)
  C) 32 / 8 groups  / top-2                   (matched-strength baseline)

Decomposition (multiplicative):  rho(A)/rho(C) = [rho(A)/rho(B)] x [rho(B)/rho(C)]
  - rho(A)/rho(B)  = pure best-third-rule effect (field/groups/draw held fixed)
  - rho(B)/rho(C)  = field-size + group-count effect (both top-2-only)
Plus the cross-group share, which is created *only* by the best-third pool (0 in B and C).

Usage:
  uv run python scripts/run_decomposition.py --snapshots 160 --inner 150
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wc2026 import data, fit_elo
from src.wc2026.formats import SPEC_32, SPEC_48, SPEC_48_TOP2
from src.wc2026.samplers import EloSampler
from scripts.run_manipulability import build_field, evaluate_format, bootstrap_ci, ratio_ci


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", type=int, default=160)
    ap.add_argument("--inner", type=int, default=150)
    ap.add_argument("--margin", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=str, default="results/decomposition.json")
    args = ap.parse_args()

    print("[1/4] fitting Elo + loading official draw ...")
    df = data.load_results()
    model, _ = fit_elo.fit(df)
    sampler = EloSampler(model)
    official_groups = data.load_draw()["groups"]
    field48 = [t for g in official_groups for t in g]
    r48 = {t: i for i, t in enumerate(sorted(field48, key=model.rating, reverse=True))}
    f32, r32 = build_field(model, 32)

    ns, ni, mg = args.snapshots, args.inner, args.margin
    print(f"[2/4] arm A: 48 top-2 + best-third (real format)  [{ns}x{ni}] ...")
    mA, cA, sA = evaluate_format(SPEC_48, field48, r48, sampler, ns, ni, mg, args.seed,
                                 groups=official_groups)
    print(f"[3/4] arm B: 48 top-2 ONLY (rule toggled off)      [{ns}x{ni}] ...")
    mB, cB, sB = evaluate_format(SPEC_48_TOP2, field48, r48, sampler, ns, ni, mg, args.seed,
                                 groups=official_groups)
    print(f"[4/4] arm C: 32 top-2 (matched baseline)           [{ns}x{ni}] ...")
    mC, cC, sC = evaluate_format(SPEC_32, f32, r32, sampler, ns, ni, mg, args.seed + 1)

    boot = np.random.default_rng(args.seed + 99)

    def arm(label, m, c, s):
        rho, lo, hi = bootstrap_ci(m, s, rng=boot)
        cg = c.sum() / m.sum() if m.sum() > 0 else 0.0
        return {"label": label, "rho": rho, "rho_ci": [lo, hi],
                "cross_group_share": cg, "n_states": int(len(m)), "n_manip": int(m.sum())}

    A = arm("48 top-2 + best-third (real)", mA, cA, sA)
    B = arm("48 top-2 only", mB, cB, sB)
    C = arm("32 top-2 (baseline)", mC, cC, sC)

    def ratio(num, snum, den, sden):
        pt, lo, hi = ratio_ci(num, snum, den, sden, rng=boot)
        return {"point": pt, "ci": [lo, hi]}

    decomp = {
        "overall_multiplier_A_over_C": ratio(mA, sA, mC, sC),      # rho(48 real)/rho(32)
        "best_third_effect_A_over_B": ratio(mA, sA, mB, sB),       # pure rule effect
        "field_group_effect_B_over_C": ratio(mB, sB, mC, sC),      # field+group-count effect
    }

    out = {"meta": {"snapshots": ns, "inner": ni, "margin": mg, "seed": args.seed,
                    "draw": "official 2026 for 48-arms; matched-strength for 32"},
           "arms": {"A": A, "B": B, "C": C}, "decomposition": decomp}
    outpath = Path(args.out)
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(json.dumps(out, indent=2))

    print(f"\n=== factorial decomposition (snapshots={ns} inner={ni} margin={mg}) ===")
    for X in (A, B, C):
        print(f"  {X['label']:<32} rho={X['rho']:.3f} [{X['rho_ci'][0]:.3f}, {X['rho_ci'][1]:.3f}]"
              f"  cross_group_share={X['cross_group_share']:.3f}  (n={X['n_states']})")
    print()
    d = decomp
    print(f"  overall multiplier  rho(48 real)/rho(32) = {d['overall_multiplier_A_over_C']['point']:.2f} "
          f"[{d['overall_multiplier_A_over_C']['ci'][0]:.2f}, {d['overall_multiplier_A_over_C']['ci'][1]:.2f}]")
    print(f"  -> best-third rule  rho(A)/rho(B)         = {d['best_third_effect_A_over_B']['point']:.2f} "
          f"[{d['best_third_effect_A_over_B']['ci'][0]:.2f}, {d['best_third_effect_A_over_B']['ci'][1]:.2f}]"
          f"   (field/groups/draw fixed)")
    print(f"  -> field+group-count rho(B)/rho(C)        = {d['field_group_effect_B_over_C']['point']:.2f} "
          f"[{d['field_group_effect_B_over_C']['ci'][0]:.2f}, {d['field_group_effect_B_over_C']['ci'][1]:.2f}]")
    print(f"\n  cross-group share: {A['cross_group_share']:.0%} (best-third) vs "
          f"{B['cross_group_share']:.0%} (top-2-only) vs {C['cross_group_share']:.0%} (32) "
          f"-> the cross-group mechanism is created ONLY by the best-third rule.")
    print(f"\ndata -> {outpath}")


if __name__ == "__main__":
    main()
