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

**Expansion multiplier ρ(48)/ρ(32) = 1.64 [1.40, 1.97].** *(CIs here use the naive per-state
bootstrap; superseded by R7's cluster bootstrap — corrected intervals are essentially identical.)*

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

**Expansion multiplier ρ(48)/ρ(32) = 1.74 [1.48, 2.09].** *(CI methodology superseded by R7's
cluster bootstrap: corrected = 1.69 [1.44, 2.04], conclusion unchanged.)*

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
**Setup:** conditions on the **16 of 24 MD1 matches played so far** (MD1 is not yet complete; the
remaining 8 MD1 matches and all of MD2 are simulated), uses the official matchday schedule, and
projects each group to its real MD3 over 60 Monte-Carlo continuations (Elo). Artifact:
`results/r4_named.json`. *(Earlier wording "the 16 real MD1 results" wrongly implied a complete
matchday — corrected per reviewer R2.)*

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
continuations; the ranked magnitudes are the falsifiable predictions. In the cross-group cases
(e.g. Brazil–Scotland), the flagged team's qualification routes through the best-third pool, so its
advancement-optimal result depends on other groups and is not removed by simultaneous kickoffs.

**Caveat / freeze timing:** MD2 has not yet been played (starts ~June 18), so these projections
average over simulated MD2 outcomes. The **sharpest, lowest-variance freeze** is right after MD2
completes and just before MD3 (~June 23–24), when only the MD3 results remain uncertain. Treat R4
as the early projection; re-run + OSF-freeze post-MD2.

---

## R5 — Cross-model robustness of the named predictions (2026-06-17)

**Commands:**
`uv run python scripts/run_r4_named.py --model elo    --snapshots 60 --inner 150 --margin 0.05` (= R4)
`uv run python scripts/run_r4_named.py --model poisson --snapshots 60 --inner 150 --margin 0.05`
**Setup:** identical R4 projection (partial real MD1 — 16/24 — official MD3, conditioned-on continuations) run under
two **independent strength-model families** — full-history Elo vs. a hierarchical Bayesian Poisson
(Dixon–Coles, post-2018 window, **non-centered, 4 chains**). This addresses the #1 reviewer attack
and the #1 documented freeze caveat: that the named predictions are an Elo artifact. Artifacts:
`results/r4_named.json` (Elo), `results/r4_named_poisson.json` (Poisson).

**Poisson convergence (converged fit).** Non-centered parameterization (`*_raw` × group sd) +
4 chains / tune=1500 / target_accept=0.95. **All 48 field teams: max r-hat = 1.000, min ESS = 2413,
0 divergences.** The only residual r-hat > 1.01 across all 572 params is a single data-poor non-field
team (r-hat 1.02), irrelevant to the analysis. (Earlier 2-chain centered fit warned widely — fixed.)

**Agreement across the 24 MD3 matches:**

| Quantity | Spearman ρ | Pearson r |
|----------|-----------:|----------:|
| P(manipulable) | **0.90** | 0.91 |
| P(cross-group) | 0.79 | — |

Robust set (P(manip) ≥ 0.50 **under both models**, per PREREGISTRATION §5): **7 matches**, Jaccard
0.64 vs. either model's ≥0.50 set.

| P(manip) elo/pois | P(cross) elo/pois | Group | MD3 match |
|:-----------------:|:-----------------:|:-----:|-----------|
| 73% / 70% | 23% / 18% | E | Germany vs Ivory Coast |
| 68% / 72% | 33% / 30% | K | Colombia vs Portugal |
| 65% / 67% | **48% / 48%** | C | Brazil vs Scotland |
| 63% / 55% | 28% / 30% | F | Netherlands vs Sweden |
| 60% / 52% | 22% / 18% | I | France vs Norway |
| 53% / 53% | 22% / 13% | J | Argentina vs Jordan |
| 53% / 53% | 20% / 12% | L | England vs Panama |

**Model-disagreement** in the ≥0.50 band (all *near*-threshold, not contradictory): Czech Republic–
Mexico (A, 60/43%), Canada–Switzerland (B, 55/47%), Turkey–USA (D, 53/47%) clear the bar under Elo
only; Australia–Paraguay (D, 47/52%) under Poisson only. **Brazil–Scotland remains the strongest
cross-group case under both models (48%/48%)** — the headline simultaneity-proof prediction.

**Reading:** the named predictions are **not** a single-model artifact — rank order is preserved
across two independent model families (ρ = 0.90, *up* from 0.86 with the converged fit), and the
registered robust set is what we freeze. So the prediction does not depend on the Elo specification.
*(Caveat per reviewers: Elo and Bayesian-Poisson are both goals models and not fully independent;
"model-family stability" is the correct claim, not model-class independence.)*

**Freeze caveats (remaining):**
1. ✅ **Resolved** — Poisson convergence fixed via non-centered reparameterization (above).
2. Still pre-MD2 — re-run both arms conditioned on real MD1+MD2 at the freeze (~June 23–24).
3. ✅ **Resolved** — q3/margin sensitivity done (R6 below).

---

## R6 — Margin (q3) sensitivity of the named predictions (2026-06-17)

**Command:** `uv run python scripts/run_q3_sensitivity.py --snapshots 60 --inner 150`
**Setup:** the R4 projection run **once per model**, capturing each team's raw decision
record (adv_action, Δ, q3_adv) per snapshot, then re-thresholded at margins {0.03, 0.05, 0.08}
*without* re-running the sub-simulations (enabled by exposing `q3_adv` on `ManipResult`). The
cross-group flag threshold is held at 0.05. Artifact: `results/q3_sensitivity.json`. This is the
sensitivity analysis pre-committed in PREREGISTRATION §4.

**Rank stability of P(manipulable) across margins (Spearman ρ vs. margin 0.05):**

| Model | 0.05 vs 0.03 | 0.05 vs 0.08 |
|-------|-------------:|-------------:|
| Elo | **0.986** | **0.978** |
| Bayesian Poisson | **0.975** | **0.979** |

**Robust-set (P ≥ 0.50) size by margin:** Elo 13 / 10 / 5; Poisson 12 / 8 / 3 (at 0.03 / 0.05 / 0.08).

**Reading:** the **ranking** of MD3 matches — i.e. the actual prediction — is essentially
invariant to the margin (ρ ≈ 0.98 throughout, both models). Absolute manipulability *levels*
fall as the margin tightens (by construction: a stricter Δ band flags fewer states), which shrinks
the ≥0.50 set; but the **headline matches persist across all three margins and both models**:
Germany–Ivory Coast, Colombia–Portugal, Brazil–Scotland, Netherlands–Sweden, and France–Norway are
in the top tier at every setting. The conclusions do not hinge on the choice of margin; only the
borderline set-membership does, which we report honestly rather than fix to a single threshold.

**Net status:** with R5 (cross-model) and R6 (cross-margin), the two methodological freeze caveats
are closed. The only remaining pre-freeze step is the post-MD2 re-run on real results (~June 23–24).

---

## R7 — Cluster-bootstrap correction to the CIs (2026-06-17)

**Trigger:** the LLM-judge review panel (methodologist reviewer) flagged that R2/R3 bootstrap
the 95% CIs *over individual match-states*, but states within one Monte-Carlo snapshot share the
same simulated MD1–2 results and are therefore **correlated** — the i.i.d. per-state resample
understates the CIs. **Fix:** `run_manipulability.py` now uses a **cluster bootstrap** that resamples
whole snapshots (the independent unit) for both the per-format ρ and the multiplier ratio.

**Command:** `uv run python scripts/run_manipulability.py --official --snapshots 30 --inner 200 --margin 0.05`

| Format | ρ (per-state CI, old) | ρ (cluster CI, corrected) |
|--------|----------------------:|--------------------------:|
| 32-team | 0.152 [0.131, 0.174] | 0.152 [0.129, 0.174] |
| 48-team | 0.264 [0.240, 0.287] | 0.258 [0.237, 0.278] |

**Expansion multiplier ρ(48)/ρ(32) = 1.69 [1.44, 2.04]** (was 1.74 [1.48, 2.09]).

**Reading:** the correct cluster bootstrap leaves the CIs **essentially unchanged** — within-snapshot
correlation of the binary manipulability indicator is modest relative to 30 snapshots. The headline
conclusion is unaffected: the multiplier point estimate is ~1.7 and its **95% CI still excludes 1.0**.
The methodology is now correct *and* the result is shown robust to the correction — a direct, clean
answer to the reviewer's (valid) statistical objection. **All CIs reported henceforth (and at the
freeze) use the cluster bootstrap; the R2/R3 interval figures are superseded by this entry.**

---

## R8 — Monte-Carlo convergence of the multiplier + budget decision (2026-06-17)

**Trigger:** the methodologist reviewer (R3) argued 30 snapshots (R7) / 60 (R4–R6) under-sample the
MD1–2 history space, so the cluster-bootstrap CIs may not have converged; and there was an internal
inconsistency (PREREGISTRATION §3 said snapshots ≥ 60, R7 used 30). **Test:** evaluate both formats
once at 400 snapshots (official draw, inner=150), then compute the multiplier + cluster CI on
increasing snapshot *prefixes* (snapshots are i.i.d., so this gives the whole convergence curve from
one pass). Artifacts: `results/convergence.json`, `results/convergence.png`.

**Command:** `uv run python scripts/run_convergence.py --official --max-snapshots 400 --inner 150`

| snapshots | multiplier | 95% CI | CI width |
|----------:|-----------:|:------:|---------:|
| 10  | 1.73 | [1.32, 2.35] | 1.03 |
| 20  | 1.46 | [1.21, 1.80] | 0.59 |
| 40  | 1.47 | [1.30, 1.67] | 0.37 |
| 80  | 1.57 | [1.44, 1.71] | 0.28 |
| 160 | 1.55 | [1.47, 1.64] | 0.18 |
| 240 | 1.61 | [1.53, 1.69] | 0.16 |
| 320 | 1.63 | [1.56, 1.70] | 0.15 |
| **400** | **1.64** | **[1.58, 1.71]** | **0.125** |

**Reading:** the point estimate is noisy below ~40 snapshots (1.73→1.46→1.47) — R7's 30-snapshot run
sat in that unstable regime — then **stabilizes from N≈80** and settles at **1.64 [1.58, 1.71]** by
N=400. CI width shrinks ∝ 1/√N (proper sampling convergence) and the **95% CI excludes 1.0 at every
budget tested (N≥10)**. R3's concern was correct in direction (low-N estimates are noisy) but the
qualitative conclusion never flips.

**New headline (supersedes R7's 30-snapshot 1.69):** **ρ(48)/ρ(32) = 1.64 [1.58, 1.71]** at N=400.

**Budget decision:** the freeze uses **≥400 snapshots, ≥150 inner** — convergence-justified (point
estimate flat to ±0.03 and CI width <0.13 by N=400; demonstrated feasible). PREREGISTRATION §3 updated
accordingly, resolving the ≥60-vs-30 inconsistency. This closes R3's Monte-Carlo-budget critique.

---

## R9 — Factorial decomposition: the multiplier is the *rule*, not the *size* (2026-06-17)

**Trigger:** reviewers R1 & R2 (finding C3) noted the headline multiplier ρ(48)/ρ(32) conflates ≥4
simultaneous changes — the best-third wildcard rule, the field size (32→48), the group count (8→12),
and the draw — so it is **not causally identified** as an effect of "expansion." **Test:** a 3-arm
factorial that isolates the best-third rule by holding the field, groups, and draw fixed and toggling
*only* the advancement rule. Required `SPEC_48_TOP2` (real 48 field/12 groups, top-2 only → 24
qualifiers) + bye-padded knockout brackets (`simulator._seed_bracket`). Artifact:
`results/decomposition.json`.

**Command:** `uv run python scripts/run_decomposition.py --snapshots 160 --inner 150 --margin 0.05`

| Arm | Format (field / groups / rule) | ρ | cross-group share |
|-----|--------------------------------|---:|------------------:|
| A | 48 / 12 / top-2 **+ 8 best-thirds** (real, official draw) | 0.266 [0.258, 0.274] | **0.495** |
| B | 48 / 12 / **top-2 only** (same field+groups+draw) | 0.155 [0.148, 0.161] | 0.000 |
| C | 32 / 8 / top-2 (matched-strength baseline) | 0.157 [0.149, 0.166] | 0.000 |

**Multiplicative decomposition** ρ(A)/ρ(C) = [ρ(A)/ρ(B)] × [ρ(B)/ρ(C)]:

| Component | Ratio | 95% CI | Meaning |
|-----------|------:|:------:|---------|
| Overall multiplier ρ(A)/ρ(C) | **1.69** | [1.59, 1.80] | the headline number |
| **Best-third rule** ρ(A)/ρ(B) | **1.72** | [1.63, 1.81] | **field/groups/draw held fixed** |
| Field + group-count ρ(B)/ρ(C) | 0.98 | [0.92, 1.06] | both top-2-only; CI **spans 1.0** |

**Reading — this is the identification result the thesis needs:**
- The manipulability increase is attributable **almost entirely to the best-third wildcard rule**
  (1.72×), *not* to having more teams or more groups: the pure field-size + group-count effect is
  **0.98 [0.92, 1.06] — statistically indistinguishable from no effect**.
- The **cross-group mechanism is created solely by the rule**: cross-group share is **49%** with
  best-thirds but **identically 0%** in both top-2-only arms (B and C). Expanding the field without
  the wildcard rule produces *no* simultaneity-irreducible manipulability.
- The official-draw multiplier (R8: 1.64; here 1.69) is therefore best read as a **case study**; the
  **identified causal quantity is the rule effect, 1.72**. This directly answers C3: "expansion" per
  se is not the cause — the best-third advancement *rule* is.

**Net:** strongest single result for the paper's mechanism claim — it converts "expansion correlates
with manipulability" into "the best-third rule *causes* it, and uniquely creates the cross-group,
simultaneity-proof variety." Closes reviewer finding C3.
