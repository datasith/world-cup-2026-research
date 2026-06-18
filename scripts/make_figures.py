"""Generate the manuscript figures from the committed result artifacts.

Reproducible: reads results/{decomposition,convergence,r4_freeze_*}.json and writes
publication-ready PDFs to paper/figures/. Run: uv run python scripts/make_figures.py

Figures:
  fig1_rates.pdf        manipulability rate rho and cross-group share by format arm
  fig2_decomposition.pdf the multiplier decomposed into rule vs field effects (CIs)
  fig3_predictions.pdf   named MD3 predictions: P(manipulable) per match, both models
  figS_convergence.pdf   (supplementary) multiplier vs Monte-Carlo snapshot budget
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
REPO = Path(__file__).resolve().parents[1]
RES = REPO / "results"
OUT = REPO / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.spines.top": False,
    "axes.spines.right": False, "figure.dpi": 140, "savefig.bbox": "tight",
})
C48, C32, CRULE, CX = "#1f77b4", "#9aa0a6", "#d1495b", "#2a9d8f"


def _load(name):
    return json.loads((RES / name).read_text())


def fig1_rates():
    d = _load("decomposition.json")["arms"]
    order = [("C", "32-team\n(top 2)"), ("B", "48-team\n(top 2 only)"), ("A", "48-team\n(+ best third)")]
    rho = [d[k]["rho"] for k, _ in order]
    lo = [d[k]["rho"] - d[k]["rho_ci"][0] for k, _ in order]
    hi = [d[k]["rho_ci"][1] - d[k]["rho"] for k, _ in order]
    xg = [d[k]["cross_group_share"] for k, _ in order]
    labels = [lbl for _, lbl in order]
    colors = [C32, C48, C48]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.2))
    x = np.arange(3)
    ax1.bar(x, rho, yerr=[lo, hi], color=colors, capsize=4, width=0.6)
    ax1.set_xticks(x); ax1.set_xticklabels(labels)
    ax1.set_ylabel(r"manipulability rate $\rho$")
    ax1.set_title("(a) Final-matchday manipulability", fontsize=10, loc="left")
    for xi, v in zip(x, rho):
        ax1.text(xi, v + 0.012, f"{v:.2f}", ha="center", fontsize=9)
    ax1.set_ylim(0, max(rho) * 1.25)

    ax2.bar(x, xg, color=[CX if v > 0 else "#cccccc" for v in xg], width=0.6)
    ax2.set_xticks(x); ax2.set_xticklabels(labels)
    ax2.set_ylabel("cross-group share of\nmanipulable states")
    ax2.set_title("(b) Simultaneity-irreducible share", fontsize=10, loc="left")
    for xi, v in zip(x, xg):
        ax2.text(xi, v + 0.012, f"{v:.0%}", ha="center", fontsize=9)
    ax2.set_ylim(0, max(0.6, max(xg) * 1.25))
    fig.tight_layout(); fig.savefig(OUT / "fig1_rates.pdf"); plt.close(fig)


def fig2_decomposition():
    d = _load("decomposition.json")["decomposition"]
    rows = [
        ("Field + group count\n" + r"$\rho_B/\rho_C$", d["field_group_effect_B_over_C"]),
        ("Best-third rule\n" + r"$\rho_A/\rho_B$", d["best_third_effect_A_over_B"]),
        ("Overall multiplier\n" + r"$\rho_A/\rho_C$", d["overall_multiplier_A_over_C"]),
    ]
    y = np.arange(len(rows))
    pts = [r[1]["point"] for r in rows]
    lo = [r[1]["point"] - r[1]["ci"][0] for r in rows]
    hi = [r[1]["ci"][1] - r[1]["point"] for r in rows]
    colors = [C32, CRULE, C48]

    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    ax.axvline(1.0, ls="--", color="grey", lw=1, zorder=0, label="no effect (=1)")
    ax.errorbar(pts, y, xerr=[lo, hi], fmt="o", capsize=4, ms=7,
                color="black", ecolor="black", zorder=3)
    for yi, p, c in zip(y, pts, colors):
        ax.scatter([p], [yi], s=70, color=c, zorder=4)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("effect on manipulability rate (ratio)")
    ax.set_title("Decomposition of the expansion multiplier", fontsize=10, loc="left")
    for yi, p in zip(y, pts):
        ax.text(p, yi + 0.18, f"{p:.2f}", ha="center", fontsize=9)
    ax.set_xlim(0.8, max(pts) + max(hi) + 0.2)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig2_decomposition.pdf"); plt.close(fig)


def fig3_predictions():
    elo = {(m["group"], m["match"]): m for m in _load("r4_freeze_elo.json")["matches"]}
    pois = {(m["group"], m["match"]): m for m in _load("r4_freeze_poisson.json")["matches"]}
    keys = sorted(set(elo) & set(pois),
                  key=lambda k: -(elo[k]["p_manipulable"] + pois[k]["p_manipulable"]) / 2)
    keys = keys[:12]
    labels = [f"{k[1]}  ({k[0]})" for k in keys]
    e = [elo[k]["p_manipulable"] for k in keys]
    p = [pois[k]["p_manipulable"] for k in keys]
    exg = [elo[k]["p_cross_group"] for k in keys]
    pxg = [pois[k]["p_cross_group"] for k in keys]
    y = np.arange(len(keys))[::-1]
    h = 0.38

    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.barh(y + h / 2, e, height=h, color=C48, label="Elo: P(manip)")
    ax.barh(y - h / 2, p, height=h, color="#7fb3d5", label="Poisson: P(manip)")
    ax.barh(y + h / 2, exg, height=h, color=CX, alpha=0.95, label="of which cross-group")
    ax.barh(y - h / 2, pxg, height=h, color=CX, alpha=0.6)
    ax.axvline(0.5, ls="--", color="grey", lw=1, label="robust threshold (0.50)")
    ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("P(match contains a manipulable team)")
    ax.set_title("Pre-registered MD3 predictions (frozen, official bracket)", fontsize=10, loc="left")
    ax.set_xlim(0, 1)
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "fig3_predictions.pdf"); plt.close(fig)


def figS_convergence():
    c = _load("convergence.json")["curve"]
    ks = [r["snapshots"] for r in c]
    mult = [r["multiplier"] for r in c]
    lo = [r["multiplier_ci"][0] for r in c]
    hi = [r["multiplier_ci"][1] for r in c]
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    ax.fill_between(ks, lo, hi, alpha=0.2, color=C48, label="95% cluster-bootstrap CI")
    ax.plot(ks, mult, "o-", color=C48, label=r"multiplier $\rho_{48}/\rho_{32}$")
    ax.axhline(1.0, ls="--", color="grey", lw=1, label="no effect (=1)")
    ax.set_xlabel("number of snapshots (outer Monte-Carlo)")
    ax.set_ylabel("expansion multiplier")
    ax.set_title("Monte-Carlo convergence of the multiplier", fontsize=10, loc="left")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "figS_convergence.pdf"); plt.close(fig)


def main():
    fig1_rates(); fig2_decomposition(); fig3_predictions(); figS_convergence()
    print("wrote:", *(p.name for p in sorted(OUT.glob("*.pdf"))))


if __name__ == "__main__":
    main()
