# Results log

Running record of headline numbers as the analysis matures. Each entry notes the
exact config and its caveats so we never confuse a preliminary number with a
publication/freeze number.

---

## R1 — First manipulability contrast (2026-06-16)

**Command:** `uv run python scripts/run_manipulability.py --snapshots 4 --inner 60 --margin 0.05`
**Strength model:** Elo (full-history fit), Elo scoreline sampler. Field = top-N teams
by Elo, snake-drafted into groups (stand-in for the official draw).

| Format | ρ (manipulability rate) | mean Δ | cross-group share | n states |
|--------|------------------------:|-------:|------------------:|---------:|
| 32-team | 0.133 | 0.182 | 0.000 | 128 |
| 48-team | 0.271 | 0.215 | 1.000 | 192 |

**Expansion multiplier ρ(48)/ρ(32) ≈ 2.04.** Runtime ~20 s.

**Reading:** the expanded format roughly **doubles** the rate of final-matchday states
where a team's advancement-optimal action is not to win — and under 48 teams the
cross-group share is non-zero where under 32 it is zero, i.e. the new manipulability is
of a kind that within-group simultaneous kickoffs *cannot* remove. This is exactly the
structural mechanism in THEORY.md.

**Caveats (do not quote R1 as a final number):**
1. **`depends_on_other_groups` is a conservative stub** — currently returns True for *any*
   48-team manipulable state, so cross-group-share = 1.000 is an upper bound, not yet a
   measured quantity. *Top-priority refinement:* test whether the specific team's
   advancement actually routes through a third-place/best-third (cross-group) dependency.
2. **Synthetic draw**, not the official 2026 draw. Replace before the freeze.
3. **Monte-Carlo noise** — inner=60, snapshots=4 are small; no confidence intervals yet.
   Scale up (inner≥500, snapshots≥50) and bootstrap CIs for the reported number.
4. **Elo only** — re-run under the Bayesian Poisson model for the robustness cross-check.
5. **Δ units** = expected knockout rounds won; interpret accordingly.

**Next:** refine caveat (1), then scale (3) — that gives the first defensible number.

---

## R2 — Measured cross-group flag + scaled run with CIs (2026-06-16)

**Command:** `uv run python scripts/run_manipulability.py --snapshots 30 --inner 200 --margin 0.05`
**Strength model:** Elo (full-history), Elo sampler. Field = top-N by Elo, snake-drafted
(synthetic draw, still). Runtime ~3m47s. 95% CIs by bootstrap over states.

| Format | ρ (manipulability rate) | cross-group share | n states | n manip |
|--------|------------------------:|------------------:|---------:|--------:|
| 32-team | 0.152 [0.131, 0.174] | 0.000 | 960 | 146 |
| 48-team | 0.250 [0.229, 0.273] | 0.500 | 1440 | 360 |

**Expansion multiplier ρ(48)/ρ(32) = 1.64 [1.40, 1.97].**

**Reading:**
- The expansion raises the final-matchday manipulability rate by **~64% (CI excludes 1.0
  → significant)**: from ~15% to ~25% of decisions where not-winning is advancement-optimal.
- **Half of the 48-team manipulable states are cross-group** — they route through the
  best-third-placed pool, the mechanism that within-group simultaneity cannot remove. In
  the 32-team format this share is **identically zero** (no best-third pool). This is now a
  *measured* quantity (R1's 1.000 was a stub artifact), and it is the paper's core
  structural claim.

**What improved vs R1:** caveat (1) fixed (cross-group is measured, not assumed); CIs added;
n scaled ~10x. **Remaining caveats:** still a synthetic draw (not official 2026), Elo-only
(owe Bayesian-Poisson robustness re-run), single q3 threshold (0.05) — should show
sensitivity to it. These are the path to the freeze number.

---

## R3 — Official 2026 draw (2026-06-16)

**Command:** `uv run python scripts/run_manipulability.py --official --snapshots 30 --inner 200 --margin 0.05`
**Change vs R2:** the 48-team arm now uses the **real 2026 group draw** (12 official groups,
48 teams) instead of a synthetic snake-draft. 32-team arm unchanged (matched-strength
baseline). Elo sampler. Runtime ~4m. MD1-2 simulated (real results not yet conditioned on).

| Format | ρ (manipulability rate) | cross-group share | n states |
|--------|------------------------:|------------------:|---------:|
| 32-team | 0.152 [0.131, 0.174] | 0.000 | 960 |
| 48-team | 0.264 [0.240, 0.287] | 0.484 | 1440 |

**Expansion multiplier ρ(48)/ρ(32) = 1.74 [1.48, 2.09].**

**Reading:** the result **holds and slightly strengthens** on the real draw (1.74 vs R2's 1.64;
CI still excludes 1.0). Consistent with FIFA's pot system producing strength-lopsided groups
that breed more best-third / dead-rubber scenarios. ~48% of 48-team manipulable states are
cross-group; structurally 0% under 32 teams.

**Remaining for the freeze:** (a) condition on real results to date + use the official matchday
schedule (in progress — MD3 pairings being added to the draw file); (b) Bayesian-Poisson
robustness re-run; (c) q3-threshold sensitivity.

---

## R4 — Named manipulable MD3 matches, real field (2026-06-16)

**Command:** `uv run python scripts/run_r4_named.py --snapshots 60 --inner 150 --margin 0.05`
**Setup:** conditions on the 16 real MD1 results, uses the official matchday schedule, projects
each group to its real MD3 over 60 Monte-Carlo continuations (Elo). Artifact: `results/r4_named.json`.

**Top named predictions — P(match contains a manipulable team):**

| P(manip) | P(cross-group) | Group | MD3 match |
|---------:|---------------:|:-----:|-----------|
| 73% | 23% | E | Germany vs Ivory Coast |
| 68% | 33% | K | Colombia vs Portugal |
| 65% | **48%** | C | Brazil vs Scotland |
| 63% | 28% | F | Netherlands vs Sweden |
| 60% | 30% | A | Czech Republic vs Mexico |
| 60% | 22% | I | France vs Norway |

**Strongest cross-group (simultaneity-proof) team-level cases:** Scotland (C, 33%), Colombia
(K, 23%), South Korea (A, 23%), Canada (B, 23%), Sweden (F, 22%), Algeria (J, 22%).

**Reading:** every one of the 24 MD3 matches shows some manipulation probability across
continuations; the ranked magnitudes are the falsifiable predictions. The cross-group cases
(e.g. Brazil–Scotland) are the novel mechanism — incentives that hinge on the best-third pool
and survive simultaneous kickoffs.

**Caveat / freeze timing:** MD2 has not yet been played (starts ~June 18), so these projections
average over simulated MD2 outcomes. The **sharpest, lowest-variance freeze** is right after MD2
completes and just before MD3 (~June 23–24), when only the MD3 results remain uncertain. Treat R4
as the early projection; re-run + OSF-freeze post-MD2.

---

## R5 — Cross-model robustness of the named predictions (2026-06-17)

**Commands:**
`uv run python scripts/run_r4_named.py --model elo    --snapshots 60 --inner 150 --margin 0.05` (= R4)
`uv run python scripts/run_r4_named.py --model poisson --snapshots 60 --inner 150 --margin 0.05`
**Setup:** identical R4 projection (real MD1, official MD3, conditioned-on continuations) run under
two **independent strength-model families** — full-history Elo vs. a hierarchical Bayesian Poisson
(Dixon–Coles, post-2018 window). This addresses the #1 reviewer attack and the #1 documented freeze
caveat: that the named predictions are an Elo artifact. Artifacts: `results/r4_named.json` (Elo),
`results/r4_named_poisson.json` (Poisson).

**Agreement across the 24 MD3 matches:**

| Quantity | Spearman ρ | Pearson r |
|----------|-----------:|----------:|
| P(manipulable) | **0.86** | 0.89 |
| P(cross-group) | 0.74 | — |

Robust set (P(manip) ≥ 0.50 **under both models**, per PREREGISTRATION §5): **8 matches**, Jaccard
0.67 vs. either model's top-10 alone.

| P(manip) elo/pois | P(cross) elo/pois | Group | MD3 match |
|:-----------------:|:-----------------:|:-----:|-----------|
| 73% / 83% | 23% / 18% | E | Germany vs Ivory Coast |
| 68% / 68% | 33% / 28% | K | Colombia vs Portugal |
| 65% / 65% | **48% / 40%** | C | Brazil vs Scotland |
| 60% / 63% | 22% / 25% | I | France vs Norway |
| 63% / 58% | 28% / 30% | F | Netherlands vs Sweden |
| 55% / 53% | 37% / 33% | B | Canada vs Switzerland |
| 53% / 53% | 22% / 12% | J | Argentina vs Jordan |
| 53% / 50% | 20% / 10% | L | England vs Panama |

**Only model-disagreement** in the ≥0.50 band: Czech Republic–Mexico (A, 60/43%) and
Turkey–USA (D, 53/47%) clear the bar under Elo but fall just short under Poisson — both *near* the
threshold, not contradictory. Brazil–Scotland remains the strongest cross-group case under both.

**Reading:** the named predictions are **not** a single-model artifact — rank order is preserved
across two model families (ρ = 0.86), and the registered robust set is what we freeze. This is the
robustness evidence that lifts the live test from "an Elo forecast" to a model-family-stable
prediction.

**Freeze caveats (must fix before OSF freeze):**
1. The Poisson NUTS fit threw convergence warnings (rhat > 1.01, low ESS, 2 chains). Re-fit with a
   **non-centered parameterization + ≥4 chains / more draws** for a publication-grade Poisson arm.
   The cross-model *rank* agreement is robust to this; the point P-values may shift slightly.
2. Still pre-MD2 — re-run both arms conditioned on real MD1+MD2 at the freeze (~June 23–24).
3. q3-threshold sensitivity ({0.03, 0.05, 0.08}) still owed (PREREGISTRATION §4).
