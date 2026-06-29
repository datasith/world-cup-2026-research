"""Equilibrium vs decision-theoretic manipulability across all groups (R1, increment 2).

For each group, solve the MD3 simultaneous-move game by best-response dynamics (equilibrium.py)
at the real pre-MD3 state, classify each team's equilibrium-manipulability and cross-group status,
and report the equilibrium manipulability rate and cross-group share. Compares the structural claim
(cross-group share > 0) under the equilibrium notion against the decision-theoretic baseline.

Usage: uv run python scripts/run_equilibrium.py --inner 200 --margin 0.03
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wc2026 import data, fit_elo, equilibrium as eq
from src.wc2026.engine import SimEngine
from src.wc2026.formats import SPEC_48
from src.wc2026.samplers import EloSampler

GK = "ABCDEFGHIJKL"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inner", type=int, default=200)
    ap.add_argument("--margin", type=float, default=0.03, help="min_improve for best-response")
    ap.add_argument("--max-iter", type=int, default=12)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", type=str, default="results/equilibrium.json")
    args = ap.parse_args()

    df = data.load_results()
    model, _ = fit_elo.fit(df)
    sampler = EloSampler(model)
    draw = data.load_draw()
    groups = draw["groups"]
    sr = {t: i for i, t in enumerate(sorted([t for g in groups for t in g],
                                           key=model.rating, reverse=True))}
    fixed = {(r["home"], r["away"]): (r["hg"], r["ag"])
             for r in draw["results"] if r.get("matchday") in (1, 2)}
    eng = SimEngine(groups, SPEC_48, sampler, sr, n_inner=args.inner, seed=args.seed,
                    bracket="official")

    rows = []
    n_manip = n_cross = n_teams = 0
    n_pure = 0
    for gi, teams in enumerate(groups):
        prof, status = eq.solve_group(eng, gi, teams, fixed, n_inner=args.inner,
                                      max_iter=args.max_iter, min_improve=args.margin, seed=args.seed)
        cls = eq.classify(eng, gi, teams, fixed, prof, n_inner=args.inner)
        n_pure += status == "pure_NE"
        for t in teams:
            n_teams += 1
            n_manip += cls[t]["manipulable"]
            n_cross += cls[t]["cross_group"]
            rows.append({"group": GK[gi], "team": t, "action": prof[t].value,
                         "manipulable": cls[t]["manipulable"], "cross_group": cls[t]["cross_group"],
                         "q3": round(cls[t]["q3"], 3), "status": status})
        print(f"Group {GK[gi]} [{status}]: " +
              ", ".join(f"{t}={prof[t].value}{'*' if cls[t]['cross_group'] else ''}" for t in teams))

    eq_rate = n_manip / n_teams
    eq_cross_share = (n_cross / n_manip) if n_manip else 0.0
    out = {"meta": {"inner": args.inner, "min_improve": args.margin, "seed": args.seed,
                    "state": "real pre-MD3 (MD1+MD2)", "pure_NE_groups": n_pure},
           "equilibrium_manip_rate": eq_rate, "equilibrium_cross_group_share": eq_cross_share,
           "n_teams": n_teams, "n_manip": n_manip, "n_cross": n_cross, "teams": rows}
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"\n=== equilibrium (real pre-MD3, {n_pure}/12 groups reached pure NE) ===")
    print(f"equilibrium manipulability rate: {eq_rate:.2f}  ({n_manip}/{n_teams} teams)")
    print(f"equilibrium cross-group share:   {eq_cross_share:.2f}  ({n_cross}/{n_manip})")
    print(f"-> structural claim (cross-group share > 0) under equilibrium: "
          f"{'HOLDS' if n_cross > 0 else 'does NOT hold'}")
    print(f"data -> {args.out}")


if __name__ == "__main__":
    main()
