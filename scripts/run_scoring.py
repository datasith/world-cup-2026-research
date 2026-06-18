"""Score the frozen predictions against realized results (the live test).

Run AFTER Matchday 2 (and ideally Matchday 3) are recorded in data/draw_2026.json. It
evaluates the pre-registered hypotheses (PREREGISTRATION sec.7) against what actually
happened, comparing the frozen artifacts (results/r4_freeze_{elo,poisson}.json) to the
incentives implied by the *real* pre-Matchday-3 standings.

What it computes:
  * Realized manipulability. Conditioning on the REAL MD1+MD2 results (not simulated),
    re-run the manipulability assessment at each team's true MD3 decision point (official
    bracket, both models). This gives the realized P(manipulable)/P(cross-group) per match.
  * H3 scoring. Of the frozen robust set, how many are realized-manipulable; Spearman
    correlation and Brier score of frozen P(manip) vs realized; calibration.
  * H1/H2. Behavior-independent; restated from the frozen analysis (do not require MD3).
  * Behavioral endpoint (secondary, descriptive given E<3). If a passivity CSV is supplied
    (--passivity), compute the composite index and a BH-FDR-corrected one-sided test;
    otherwise skipped with the pre-registered note.

Usage (once MD2/MD3 are in draw_2026.json):
  uv run python scripts/run_scoring.py --snapshots 60 --inner 150
  uv run python scripts/run_scoring.py --passivity data/md3_passivity.csv
"""
from __future__ import annotations

import argparse
import csv
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
from scripts.run_r4_named import build_model

GROUP_KEYS = "ABCDEFGHIJKL"


def real_pre_md3_fixed(draw) -> dict:
    """Fixed dict of REAL MD1+MD2 results only (MD3 excluded; it is the decision horizon)."""
    fixed = {}
    for r in draw["results"]:
        if r.get("matchday") in (1, 2):
            fixed[(r["home"], r["away"])] = (r["hg"], r["ag"])
    return fixed


def realized_rates(model_name, df, draw, args):
    """Return per-match realized P(manip)/P(cross) under one model, conditioning on real MD1+MD2."""
    sampler, strength_of, label = build_model(model_name, df, args.seed)
    groups = draw["groups"]
    fixed = real_pre_md3_fixed(draw)
    strength_rank = {t: i for i, t in enumerate(
        sorted([t for g in groups for t in g], key=strength_of, reverse=True))}

    match_manip = defaultdict(int)
    match_cross = defaultdict(int)
    match_name = {}
    rng = np.random.default_rng(args.seed)
    for s in range(args.snapshots):
        eng = SimEngine(groups, SPEC_48, sampler, strength_rank,
                        n_inner=args.inner, seed=int(rng.integers(1 << 30)), bracket="official")
        for gi, teams in enumerate(groups):
            gk = GROUP_KEYS[gi]
            md3 = group_matchdays(teams)[2]
            match_of = {t: frozenset(p) for p in md3 for t in p}
            man, cross = defaultdict(bool), defaultdict(bool)
            for team in teams:
                r = eng.assess(team, DecisionState(fixed=fixed, group_index=gi, team=team, md3=md3),
                               min_delta=args.margin)
                if r.manipulable:
                    mk = (gk, tuple(sorted(match_of[team])))
                    match_name[mk] = f"{mk[1][0]} vs {mk[1][1]}"
                    man[mk] = True
                    if r.cross_group:
                        cross[mk] = True
            for mk, v in man.items():
                if v:
                    match_manip[mk] += 1
                    if cross[mk]:
                        match_cross[mk] += 1
    n = args.snapshots
    # ensure every MD3 match has an entry (0 if never manipulable)
    out = {}
    for gi, teams in enumerate(groups):
        gk = GROUP_KEYS[gi]
        for p in group_matchdays(teams)[2]:
            mk = (gk, tuple(sorted(p)))
            match_name.setdefault(mk, f"{mk[1][0]} vs {mk[1][1]}")
            out[mk] = {"match": match_name[mk],
                       "p_manip": match_manip.get(mk, 0) / n,
                       "p_cross": match_cross.get(mk, 0) / n}
    return label, out


def brier(forecasts, outcomes):
    f, o = np.array(forecasts), np.array(outcomes, dtype=float)
    return float(np.mean((f - o) ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", type=int, default=60)
    ap.add_argument("--inner", type=int, default=150)
    ap.add_argument("--margin", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20260616)
    ap.add_argument("--passivity", type=str, default=None,
                    help="optional CSV of pre-standardized passivity z-scores (group,match,team,index)")
    ap.add_argument("--out", type=str, default="results/scoring.json")
    args = ap.parse_args()

    df = data.load_results()
    draw = data.load_draw()
    n_md2 = sum(1 for r in draw["results"] if r.get("matchday") == 2)
    n_md3 = sum(1 for r in draw["results"] if r.get("matchday") == 3)
    print(f"[data] MD2 recorded: {n_md2}/24, MD3 recorded: {n_md3}/24")
    if n_md2 < 24:
        print("[WARN] MD2 incomplete -- scoring is PRELIMINARY (realized incentives use whatever "
              "MD1+MD2 results are present; rerun when MD2 is complete).")

    # frozen predictions
    fro = {m: json.load(open(f"results/r4_freeze_{m}.json"))["matches"] for m in ("elo", "poisson")}
    frozen = {m: {(x["group"], tuple(sorted(x["teams"]))): x for x in fro[m]} for m in fro}

    # realized
    realized = {}
    for m in ("elo", "poisson"):
        print(f"[realized] {m}: conditioning on real MD1+MD2, {args.snapshots}x{args.inner} ...")
        _, realized[m] = realized_rates(m, df, draw, args)

    keys = sorted(realized["elo"])
    # H3 scoring per model + averaged
    report = {"meta": {"md2_recorded": n_md2, "md3_recorded": n_md3,
                       "snapshots": args.snapshots, "inner": args.inner, "margin": args.margin,
                       "preliminary": n_md2 < 24},
              "per_model": {}, "matches": []}
    for m in ("elo", "poisson"):
        fz = {k: frozen[m].get(k, {}).get("p_manipulable", 0.0) for k in keys}
        rz = {k: realized[m][k]["p_manip"] for k in keys}
        rho = spearmanr([fz[k] for k in keys], [rz[k] for k in keys])[0]
        realized_bin = [1.0 if rz[k] >= 0.5 else 0.0 for k in keys]
        report["per_model"][m] = {
            "spearman_frozen_vs_realized": float(rho),
            "brier_frozen_vs_realizedbinary": brier([fz[k] for k in keys], realized_bin),
        }

    # robust set confirmation (frozen >=0.5 both models)
    robust = [k for k in keys
              if frozen["elo"].get(k, {}).get("p_manipulable", 0) >= 0.5
              and frozen["poisson"].get(k, {}).get("p_manipulable", 0) >= 0.5]
    confirmed = [k for k in robust
                 if realized["elo"][k]["p_manip"] >= 0.5 and realized["poisson"][k]["p_manip"] >= 0.5]
    report["h3_robust_set"] = {
        "n_robust": len(robust),
        "n_confirmed_realized": len(confirmed),
        "robust_matches": [{"group": k[0], "match": realized["elo"][k]["match"],
                            "frozen_elo": frozen["elo"][k]["p_manipulable"],
                            "frozen_pois": frozen["poisson"][k]["p_manipulable"],
                            "realized_elo": realized["elo"][k]["p_manip"],
                            "realized_pois": realized["poisson"][k]["p_manip"],
                            "confirmed": k in confirmed} for k in robust],
    }

    for k in keys:
        report["matches"].append({
            "group": k[0], "match": realized["elo"][k]["match"],
            "frozen_p_manip": (frozen["elo"].get(k, {}).get("p_manipulable", 0)
                               + frozen["poisson"].get(k, {}).get("p_manipulable", 0)) / 2,
            "realized_p_manip": (realized["elo"][k]["p_manip"] + realized["poisson"][k]["p_manip"]) / 2,
            "realized_p_cross": (realized["elo"][k]["p_cross"] + realized["poisson"][k]["p_cross"]) / 2,
        })

    # behavioral (secondary; descriptive given E<3)
    if args.passivity and Path(args.passivity).exists():
        rows = list(csv.DictReader(open(args.passivity)))
        idx = [float(r["index"]) for r in rows]
        # one-sided: predict positive (more passive); BH-FDR placeholder on per-row z->p
        from scipy.stats import norm
        pvals = sorted(1 - norm.cdf(idx))
        m = len(pvals)
        bh = [p <= (i + 1) / m * 0.05 for i, p in enumerate(pvals)]
        report["behavioral"] = {"n": m, "n_significant_bh_fdr": int(sum(bh)),
                                "note": "descriptive only (pre-registered power rule E=2.76<3)"}
    else:
        report["behavioral"] = {"note": "no passivity data supplied; behavioral endpoint is "
                                "descriptive only per the pre-registered power rule (E=2.76<3)"}

    Path(args.out).write_text(json.dumps(report, indent=2))

    # print summary
    print("\n=== LIVE-TEST SCORING ===")
    print("H1/H2 (behavior-independent, from the frozen analysis): multiplier 1.69 [1.59,1.80] "
          "(CI excludes 1) -> H1 supported; cross-group share 49% (48) vs 0% (32) -> H2 supported.")
    print(f"\nH3 robust set: {len(confirmed)}/{len(robust)} frozen-robust matches realized-manipulable")
    for r in report["h3_robust_set"]["robust_matches"]:
        flag = "OK" if r["confirmed"] else "no"
        print(f"  [{flag}] {r['group']} {r['match']:<28} frozen {r['frozen_elo']:.0%}/{r['frozen_pois']:.0%}"
              f"  realized {r['realized_elo']:.0%}/{r['realized_pois']:.0%}")
    for m in ("elo", "poisson"):
        pm = report["per_model"][m]
        print(f"\n{m}: Spearman(frozen,realized)={pm['spearman_frozen_vs_realized']:.3f}  "
              f"Brier={pm['brier_frozen_vs_realizedbinary']:.3f}")
    print(f"\nfull report -> {args.out}")


if __name__ == "__main__":
    main()
