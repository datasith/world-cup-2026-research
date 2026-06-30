"""Information-regime analysis: simultaneous (headline) vs staggered (real schedule).

Addresses reviewer C6 / the "simultaneity counterfactual" blind spot (R1, R3). The
headline manipulability estimate integrates over *all* other groups' final matchday
(engine._simulate_remainder samples every non-decision match), i.e. it is the
conservative, fully-simultaneous, no-cross-group-information regime. The real 2026
schedule is *staggered* in day tiers ({A,B,C}=Jun24, {D,E,F}=Jun25, {G,H,I}=Jun26,
{J,K,L}=Jun27; data/draw_2026.json schedule[g].md3_date), so a later-tier team knows
the REAL final standings of all strictly-earlier-tier groups at its kickoff.

This script, conditioning on the REAL group stage, recomputes each team's MD3
manipulability under two information sets:
  * simultaneous: fixed = real MD1+MD2 only (other groups' MD3 sampled).
  * staggered:    fixed = real MD1+MD2 + real MD3 of all strictly-earlier-tier groups.

It reports, per regime and per day tier, the manipulability rate and cross-group share,
and an exploitability audit: of the states flagged cross-group, how many have their
deciding cross-group information already realized at kickoff (i.e. are *operationally*
exploitable, not merely structurally present). The staggered conditioning order comes
from the exact per-group MD3 kickoff times (schedule[g].md3_kickoff_et; FOX Sports
broadcast schedule), a complete temporal order over the 12 finales (B<C<A, E<F<D, I<H<G,
L<K<J). --granularity date falls back to day tiers (same-day groups simultaneous) as a
conservative robustness check.

Usage:
  uv run python scripts/run_info_regime.py --snapshots 60 --inner 150
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wc2026 import data
from src.wc2026.engine import SimEngine, DecisionState
from src.wc2026.formats import SPEC_48, group_matchdays
from scripts.run_r4_named import build_model

GROUP_KEYS = "ABCDEFGHIJKL"


def group_tiers(draw, granularity="kickoff") -> dict[int, int]:
    """Map group index -> temporal rank (earlier finale = lower rank).

    granularity='kickoff' ranks by the exact MD3 kickoff time (a total order over the 12
    group finales; same-day groups are correctly ordered) when md3_kickoff_et is present;
    'date' ranks by day only (same-day groups tie -> treated as simultaneous, conservative).
    A later-ranked group's staggered information set includes every strictly-lower-ranked
    group, so finer granularity weakly enlarges that set."""
    sched = draw["schedule"]
    key = "md3_kickoff_et" if granularity == "kickoff" else "md3_date"
    vals = {gi: sched[GROUP_KEYS[gi]].get(key) or sched[GROUP_KEYS[gi]]["md3_date"]
            for gi in range(len(draw["groups"]))}
    order = {v: r for r, v in enumerate(sorted(set(vals.values())))}
    return {gi: order[vals[gi]] for gi in vals}


def real_results_by_md(draw):
    """(home,away)->(hg,ag) dicts for MD1+MD2 and for MD3 (real, from draw['results'])."""
    md12, md3 = {}, {}
    for r in draw["results"]:
        key = (r["home"], r["away"])
        if r.get("matchday") in (1, 2):
            md12[key] = (r["hg"], r["ag"])
        elif r.get("matchday") == 3:
            md3[key] = (r["hg"], r["ag"])
    return md12, md3


def md3_fixed_for_groups(draw, md3, group_indices) -> dict:
    """Real MD3 results restricted to the given group indices (their two MD3 matches each)."""
    out = {}
    for gi in group_indices:
        teams = draw["groups"][gi]
        for (h, a) in group_matchdays(teams)[2]:
            if (h, a) in md3:
                out[(h, a)] = md3[(h, a)]
            elif (a, h) in md3:
                out[(a, h)] = md3[(a, h)]
    return out


def assess_regime(model_name, draw, args, regime: str):
    """Per-match realized P(manip)/P(cross) under one model and one info regime.

    regime: 'simultaneous' (fixed = real MD1+MD2) or 'staggered'
    (fixed = real MD1+MD2 + real MD3 of strictly-earlier-tier groups)."""
    sampler, strength_of, label = build_model(model_name, data.load_results(), args.seed)
    groups = draw["groups"]
    cond = group_tiers(draw, args.granularity)   # conditioning order (fine: by kickoff time)
    day = group_tiers(draw, "date")              # reporting bucket (coarse: 4 day tiers)
    md12, md3 = real_results_by_md(draw)
    strength_rank = {t: i for i, t in enumerate(
        sorted([t for g in groups for t in g], key=strength_of, reverse=True))}

    # staggered: precompute the strictly-earlier (by kickoff) real-MD3 fixed block per group
    earlier_fixed = {}
    for gi in range(len(groups)):
        if regime == "staggered":
            earlier = [gj for gj in range(len(groups)) if cond[gj] < cond[gi]]
            earlier_fixed[gi] = md3_fixed_for_groups(draw, md3, earlier)
        else:
            earlier_fixed[gi] = {}

    match_manip = defaultdict(int)
    match_cross = defaultdict(int)
    match_name, match_tier = {}, {}
    rng = np.random.default_rng(args.seed)
    for s in range(args.snapshots):
        eng = SimEngine(groups, SPEC_48, sampler, strength_rank,
                        n_inner=args.inner, seed=int(rng.integers(1 << 30)), bracket="official")
        for gi, teams in enumerate(groups):
            gk = GROUP_KEYS[gi]
            md3_pairs = group_matchdays(teams)[2]
            match_of = {t: frozenset(p) for p in md3_pairs for t in p}
            fixed = {**md12, **earlier_fixed[gi]}
            man, cross = defaultdict(bool), defaultdict(bool)
            for team in teams:
                r = eng.assess(team, DecisionState(fixed=fixed, group_index=gi, team=team, md3=md3_pairs),
                               min_delta=args.margin)
                if r.manipulable:
                    mk = (gk, tuple(sorted(match_of[team])))
                    match_name[mk] = f"{mk[1][0]} vs {mk[1][1]}"
                    match_tier[mk] = day[gi]
                    man[mk] = True
                    if r.cross_group:
                        cross[mk] = True
            for mk, v in man.items():
                if v:
                    match_manip[mk] += 1
                    if cross[mk]:
                        match_cross[mk] += 1
    n = args.snapshots
    out = {}
    for gi, teams in enumerate(groups):
        gk = GROUP_KEYS[gi]
        for p in group_matchdays(teams)[2]:
            mk = (gk, tuple(sorted(p)))
            match_name.setdefault(mk, f"{mk[1][0]} vs {mk[1][1]}")
            match_tier.setdefault(mk, day[gi])
            out[mk] = {"match": match_name[mk], "tier": match_tier[mk],
                       "p_manip": match_manip.get(mk, 0) / n,
                       "p_cross": match_cross.get(mk, 0) / n}
    return label, out


def sample_md3_world(draw, sampler, rng) -> dict:
    """Sample one realized MD3 for every group (each group's two final matches)."""
    world = {}
    for teams in draw["groups"]:
        for (h, a) in group_matchdays(teams)[2]:
            world[(h, a)] = sampler.sample(h, a, neutral=True, rng=rng)
    return world


def assess_format(model_name, draw, args, regime: str):
    """Format-level estimand (the 48% definition): average manipulability over simulated
    MD1-2 snapshots. For 'staggered', within each snapshot a realized MD3 is sampled and
    each team conditions on the MD3 of all strictly-earlier-kickoff groups; 'simultaneous'
    conditions on MD1-2 only. Returns per-(team,snapshot) manip/cross arrays + day-tier tags."""
    from scripts.run_manipulability import md12_snapshot
    sampler, strength_of, _ = build_model(model_name, data.load_results(), args.seed)
    groups = draw["groups"]
    cond = group_tiers(draw, args.granularity)
    day = group_tiers(draw, "date")
    strength_rank = {t: i for i, t in enumerate(
        sorted([t for g in groups for t in g], key=strength_of, reverse=True))}
    rng = np.random.default_rng(args.seed)
    manip, cross, tier, snap = [], [], [], []
    for s in range(args.snapshots):
        md12 = md12_snapshot(groups, sampler, rng)
        md3_world = sample_md3_world(draw, sampler, rng) if regime == "staggered" else {}
        eng = SimEngine(groups, SPEC_48, sampler, strength_rank,
                        n_inner=args.inner, seed=int(rng.integers(1 << 30)), bracket="official")
        for gi, teams in enumerate(groups):
            md3_pairs = group_matchdays(teams)[2]
            if regime == "staggered":
                earlier = [gj for gj in range(len(groups)) if cond[gj] < cond[gi]]
                fixed = {**md12, **md3_fixed_for_groups({"groups": groups}, md3_world, earlier)}
            else:
                fixed = md12
            for team in teams:
                r = eng.assess(team, DecisionState(fixed=fixed, group_index=gi, team=team, md3=md3_pairs),
                               min_delta=args.margin)
                manip.append(float(r.manipulable))
                cross.append(float(r.manipulable and r.cross_group))
                tier.append(day[gi])
                snap.append(s)
    return np.array(manip), np.array(cross), np.array(tier), np.array(snap)


def cluster_boot_share(manip, cross, snap, n_boot=2000, seed=0):
    """Cluster bootstrap (resample snapshots) for cross-group share = sum(cross)/sum(manip)."""
    rng = np.random.default_rng(seed)
    snaps = np.unique(snap)
    idx_by_snap = {s: np.where(snap == s)[0] for s in snaps}
    point = cross.sum() / manip.sum() if manip.sum() else 0.0
    boots = []
    for _ in range(n_boot):
        pick = rng.choice(snaps, size=len(snaps), replace=True)
        sel = np.concatenate([idx_by_snap[s] for s in pick])
        m = manip[sel].sum()
        boots.append(cross[sel].sum() / m if m else 0.0)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(point), float(lo), float(hi)


def summarize(out, threshold=0.5):
    """Overall and per-tier manipulability rate and cross-group share (match-level, P>=threshold)."""
    by_tier = defaultdict(lambda: {"manip": 0, "cross": 0, "n": 0})
    tot = {"manip": 0, "cross": 0, "n": 0}
    for mk, v in out.items():
        t = v["tier"]
        for bucket in (by_tier[t], tot):
            bucket["n"] += 1
            if v["p_manip"] >= threshold:
                bucket["manip"] += 1
                if v["p_cross"] >= threshold:
                    bucket["cross"] += 1
    def share(b):
        return {"n_matches": b["n"], "n_manip": b["manip"], "n_cross": b["cross"],
                "manip_rate": b["manip"] / b["n"] if b["n"] else 0.0,
                "cross_share": b["cross"] / b["manip"] if b["manip"] else 0.0}
    return {"overall": share(tot), "by_tier": {t: share(by_tier[t]) for t in sorted(by_tier)}}


def run_format_mode(draw, args):
    """Format-level estimand: simultaneous vs staggered cross-group share (the 48% number),
    pooled over both models, with cluster-bootstrap CIs and a day-tier breakdown."""
    DAY = ["Jun24", "Jun25", "Jun26", "Jun27"]
    out = {"meta": {"mode": "format", "granularity": args.granularity, "snapshots": args.snapshots,
                    "inner": args.inner, "margin": args.margin,
                    "note": "simultaneous = headline (all other groups sampled, the 48% regime); "
                            "staggered = each team conditions on sampled MD3 of all groups with "
                            "strictly-earlier kickoff. Cross-group share over manipulable states."},
           "regimes": {}}
    pooled = {}
    for regime in ("simultaneous", "staggered"):
        M = C = T = S = None
        for m in ("elo", "poisson"):
            print(f"[format/{regime}] {m}: {args.snapshots}x{args.inner} ...")
            man, cro, tie, snp = assess_format(m, draw, args, regime)
            if M is None:
                M, C, T, S = man, cro, tie, snp
            else:  # pool models; offset snapshot ids so clusters stay distinct
                M = np.concatenate([M, man]); C = np.concatenate([C, cro])
                T = np.concatenate([T, tie]); S = np.concatenate([S, snp + args.snapshots])
        pooled[regime] = (M, C, T, S)
        rho = float(M.mean())
        share, lo, hi = cluster_boot_share(M, C, S, seed=args.seed)
        by_tier = {}
        for t in sorted(set(T.tolist())):
            mt, ct = M[T == t], C[T == t]
            by_tier[DAY[t] if t < 4 else f"tier{t}"] = {
                "manip_rate": float(mt.mean()),
                "cross_share": float(ct.sum() / mt.sum()) if mt.sum() else 0.0}
        out["regimes"][regime] = {"manip_rate": rho, "cross_share": share,
                                  "cross_share_ci": [lo, hi], "by_tier": by_tier}

    Path(args.out.replace(".json", "_format.json")).write_text(json.dumps(out, indent=2))
    print("\n=== FORMAT-LEVEL CROSS-GROUP SHARE (the 48% estimand) ===")
    for regime in ("simultaneous", "staggered"):
        r = out["regimes"][regime]
        print(f"  {regime:<13} manip rate {r['manip_rate']:.3f}  cross-group share "
              f"{r['cross_share']:.1%}  95% CI [{r['cross_share_ci'][0]:.1%}, {r['cross_share_ci'][1]:.1%}]")
    print("\n  cross-group share by day tier (simultaneous -> staggered):")
    sim, stag = out["regimes"]["simultaneous"]["by_tier"], out["regimes"]["staggered"]["by_tier"]
    for day in [d for d in DAY if d in sim]:
        print(f"    {day}: {sim[day]['cross_share']:.0%} -> {stag[day]['cross_share']:.0%}")
    print(f"\nfull report -> {args.out.replace('.json', '_format.json')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshots", type=int, default=60)
    ap.add_argument("--inner", type=int, default=150)
    ap.add_argument("--margin", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20260616)
    ap.add_argument("--out", type=str, default="results/info_regime.json")
    ap.add_argument("--granularity", choices=("kickoff", "date"), default="kickoff",
                    help="staggered conditioning order: 'kickoff' (exact times, total order) "
                         "or 'date' (day tiers; same-day groups simultaneous, conservative)")
    ap.add_argument("--mode", choices=("realized", "format"), default="realized",
                    help="'realized': condition on real MD1-2 (exploitability audit of the actual "
                         "tournament). 'format': average over simulated MD1-2 snapshots (the 48% "
                         "estimand) -- the headline simultaneous-vs-staggered cross-group share.")
    args = ap.parse_args()

    draw = data.load_draw()
    n_md3 = sum(1 for r in draw["results"] if r.get("matchday") == 3)

    if args.mode == "format":
        return run_format_mode(draw, args)
    print(f"[data] MD3 recorded: {n_md3}/24 (staggered regime conditions on real earlier-tier MD3)")

    regimes = {}
    for regime in ("simultaneous", "staggered"):
        per_model = {}
        for m in ("elo", "poisson"):
            print(f"[{regime}] {m}: {args.snapshots}x{args.inner} ...")
            _, per_model[m] = assess_regime(m, draw, args, regime)
        # average the two models per match
        keys = sorted(per_model["elo"])
        avg = {mk: {"match": per_model["elo"][mk]["match"], "tier": per_model["elo"][mk]["tier"],
                    "p_manip": (per_model["elo"][mk]["p_manip"] + per_model["poisson"][mk]["p_manip"]) / 2,
                    "p_cross": (per_model["elo"][mk]["p_cross"] + per_model["poisson"][mk]["p_cross"]) / 2}
               for mk in keys}
        regimes[regime] = {"avg": avg, "summary": summarize(avg)}

    # exploitability audit: per match, cross-group flag under each regime
    keys = sorted(regimes["simultaneous"]["avg"])
    audit = []
    for mk in keys:
        si = regimes["simultaneous"]["avg"][mk]
        st = regimes["staggered"]["avg"][mk]
        audit.append({"group": mk[0], "match": si["match"], "tier": si["tier"],
                      "sim_p_cross": si["p_cross"], "stag_p_cross": st["p_cross"],
                      "sim_cross": si["p_cross"] >= 0.5, "stag_cross": st["p_cross"] >= 0.5,
                      "delta_cross": st["p_cross"] - si["p_cross"]})

    report = {"meta": {"snapshots": args.snapshots, "inner": args.inner, "margin": args.margin,
                       "md3_recorded": n_md3,
                       "granularity": args.granularity,
                       "note": "simultaneous = headline (all other groups sampled); staggered = "
                               "condition on real MD3 of all groups with strictly-earlier kickoff "
                               f"({args.granularity} order). Reporting tiers are the 4 day buckets."},
              "simultaneous": regimes["simultaneous"]["summary"],
              "staggered": regimes["staggered"]["summary"],
              "exploitability_audit": audit}
    Path(args.out).write_text(json.dumps(report, indent=2))

    # print
    print("\n=== INFORMATION-REGIME COMPARISON (match-level, P>=0.5) ===")
    for regime in ("simultaneous", "staggered"):
        s = regimes[regime]["summary"]["overall"]
        print(f"  {regime:<13} manip {s['n_manip']}/{s['n_matches']} "
              f"cross-group share {s['cross_share']:.0%} ({s['n_cross']}/{s['n_manip']})")
    print("\n  by tier (cross-group share, simultaneous -> staggered):")
    for t in sorted(regimes["simultaneous"]["summary"]["by_tier"]):
        si = regimes["simultaneous"]["summary"]["by_tier"][t]
        st = regimes["staggered"]["summary"]["by_tier"][t]
        day = ["Jun24", "Jun25", "Jun26", "Jun27"][t] if t < 4 else f"tier{t}"
        print(f"    tier {t} ({day}): {si['cross_share']:.0%} -> {st['cross_share']:.0%}  "
              f"(manip {si['n_manip']}->{st['n_manip']} of {si['n_matches']})")
    n_newly = sum(1 for a in audit if a["stag_cross"] and not a["sim_cross"])
    n_lost = sum(1 for a in audit if a["sim_cross"] and not a["stag_cross"])
    print(f"\n  exploitability: {n_newly} matches become cross-group manipulable under the real "
          f"staggered schedule that were not under the simultaneous bound; {n_lost} resolved.")
    print(f"\nfull report -> {args.out}")


if __name__ == "__main__":
    main()
