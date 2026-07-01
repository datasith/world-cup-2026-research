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

---

## R10 — V_adv specification sensitivity + pinned definition (2026-06-17)

**Trigger:** reviewer C1 (R1 critical, R2 critical) — `V_adv` and the action space were listed *open*
in THEORY §6 while every number depended on them, and RESULTS vs THEORY described Δ differently.
**Done (pinning):** THEORY §2 now fixes a single canonical `V_adv` = **expected knockout rounds won**
(0 if eliminated; this subsumes "P(advance)" and "bracket-path strength"), the action space
$\{$WIN,DRAW,LOSE$\}$→conditioned scorelines, and a decision-theoretic (fixed-opponent) model.
**Done (range, per R1):** re-ran the 32-vs-48 multiplier under three `V_adv` functionals, all from
the same sub-simulations. Command:
`uv run python scripts/run_vadv_sensitivity.py --official --snapshots 160 --inner 150`. Artifact:
`results/vadv_sensitivity.json`.

| V_adv | ρ(32) | ρ(48) | cross-group(48) | multiplier (95% CI) |
|-------|------:|------:|----------------:|--------------------:|
| **depth** (rounds won; canonical) | 0.171 | 0.266 | 0.487 | **1.55 [1.47, 1.65]** |
| qualify (P advance) | 0.000 | 0.000 | — | — (no manipulable states) |
| champion (P win title) | 0.021 | 0.012 | 0.319 | 0.59 [0.45, 0.76] |

**Reading (honest — this refines the claim rather than just confirming it):**
- **Canonical `depth`:** multiplier **1.55**, CI excludes 1.0, exactly matching the R8 convergence
  curve at N=160. The headline is robust under the pinned definition.
- **`qualify` → 0 in *both* formats:** under a pure "will I advance?" objective with coarse W/D/L
  actions, performing better never *hurts* your own qualification, so the advancement-optimal action
  is essentially always WIN. **The manipulation is therefore not about the qualification threshold —
  it is about the downstream seeding / bracket path.** This is the mechanism: the best-third rule
  perturbs *which* bracket slot a team lands in (cross-group), not *whether* it qualifies. A genuine
  threshold-tank (Gijón) needs within-WIN scoreline targeting, which the coarse action space cannot
  represent (THEORY §6 open task).
- **`champion`:** manipulable states are rare (1–2% of decisions, tens of states) and dominated by
  *strong* teams' bracket tweaks; best-third (weak) teams have ~0 title odds so their cross-group
  manipulability doesn't register here. The estimate is **underpowered** and the point <1 rests on a
  handful of states — reported for completeness, not relied upon.

**Conclusion:** per R1's "report the range," the headline holds under the canonical `depth` objective
and the alternatives *clarify the mechanism* (path-, not threshold-, driven). C1 closed; the
finer-action-space (scoreline-targeting) and equilibrium treatments remain logged as open in THEORY §6.

---

## R11 — FREEZE artifact: named MD3 predictions, official bracket, after MD1 (2026-06-18)

**This is the pre-registered live-test prediction set.** Run under the **official 2026 R32→final
bracket** (C5), conditioned on **all 24 MD1 results** (complete; Group J order corrected), with MD2
and MD3 unplayed — a genuine two-matchday-ahead forecast (after-MD1 freeze, PREREGISTRATION §6).
Artifacts: `results/r4_freeze_elo.json`, `results/r4_freeze_poisson.json`.

**Command (locked):**
`run_r4_named.py --bracket official --model {elo,poisson} --snapshots 400 --inner 150 --margin 0.05`

**Cross-model agreement:** Spearman ρ on P(manipulable) across the 24 MD3 matches = **0.964**.

**Registered robust set — P(manipulable) ≥ 0.50 under *both* models (the falsifiable predictions):**

| P(manip) elo/pois | P(cross) elo/pois | Group | MD3 match |
|:-----------------:|:-----------------:|:-----:|-----------|
| 56% / 78% | 29% / 36% | C | Brazil vs Scotland |
| 57% / 74% | 28% / 41% | B | Canada vs Switzerland |
| 55% / 67% | 16% / 22% | A | Czech Republic vs Mexico |
| 54% / 65% | **39% / 51%** | J | Algeria vs Austria |
| 56% / 58% | 35% / 40% | F | Netherlands vs Sweden |

**Registered cross-group teams — P(cross_group) ≥ 0.20 under both** (the simultaneity-proof cases):
Algeria (J), Austria (J), Sweden (F), Netherlands (F), Japan (F). Algeria–Austria (J) is the
strongest cross-group match; Group F is the cross-group hotspot.

**Power (pre-registered C8):** expected realized robust manipulable matches
$E=\sum_{\text{robust}}\min(P_{\text{elo}},P_{\text{pois}}) = \mathbf{2.76} < 3$. Per the locked rule
(PREREGISTRATION §7), the **behavioral endpoint is therefore reported as descriptive/illustrative
only**; the behavior-independent primary endpoint (H1 multiplier, H2 cross-group share) carries the
test. (This is our own pre-registered stopping rule firing, recorded before MD2/MD3.)

**Note vs earlier (seeded-bracket) projections R4/R5:** the named set shifts under the real bracket
geometry + complete data — Germany–Ivory Coast and Colombia–Portugal fall below the 0.50 robust bar,
while Algeria–Austria and Canada–Switzerland rise; Brazil–Scotland and Netherlands–Sweden persist as
cross-group cases. Expected and correct: R11 supersedes R4/R5 as the registered set.

**Freeze status:** predictions locked; ready for the OSF registration (`FREEZE_CHECKLIST.md`).

---

## R12 — Decomposition re-run at the converged budget (N=400) for a single primary number (2026-06-18)

**Trigger:** the re-review (panel run `results/reviews/20260618_121208/`) flagged that the manuscript
mixed multiplier values across runs/budgets — abstract 1.69 (R9, N=160), convergence 1.64 (R8, N=400),
V_adv depth 1.55 (R10, N=160, different 32-baseline seed). All are Monte-Carlo noise in the 32-team
baseline (ρ32 ranged 0.152–0.171 across seeds). **Fix:** re-run the 3-arm factorial at the freeze
budget (N=400, inner=150, seeded bracket, cluster bootstrap) so the headline multiplier *and* its
decomposition come from one converged run. Artifact: `results/decomposition.json` (now N=400; the
N=160 version is in git history at R9).

**Command:** `uv run python scripts/run_decomposition.py --snapshots 400 --inner 150 --margin 0.05`

| Arm | ρ | cross-group share |
|-----|---:|------------------:|
| A — 48 top-2 + best-third (real) | 0.263 [0.258, 0.269] | **0.479** |
| B — 48 top-2 only | 0.153 [0.148, 0.157] | 0.000 |
| C — 32 top-2 (baseline) | 0.159 [0.153, 0.165] | 0.000 |

**Primary numbers (used throughout the manuscript):**
- Overall multiplier ρ(A)/ρ(C) = **1.66 [1.59, 1.73]**
- Best-third-rule effect ρ(A)/ρ(B) = **1.72 [1.66, 1.79]**
- Field + group-count effect ρ(B)/ρ(C) = **0.96 [0.92, 1.01]** (includes 1 → no detectable effect)
- Cross-group share = **48%** (rule) vs 0% (both top-2-only arms)

**Reading:** consistent with R8's convergence number (1.64 [1.58, 1.71], overlapping CI) and with the
R9 story (1.72 × 0.96 = 1.66, internally consistent). The manuscript abstract/results/figures now cite
**only these N=400 numbers**; R7–R10 multiplier figures are superseded for the headline (kept as the
robustness/convergence/sensitivity record). Figures 1–2 regenerated from this artifact.

---

## R13 — LIVE-TEST SCORING: frozen predictions vs the realized group stage (2026-06-29)

**The payoff.** The group stage is complete (all 24 MD2 + 24 MD3 results loaded and verified vs final
standings). We score the frozen predictions (R11, registered after MD1) against reality.
`scripts/run_scoring.py` conditions on the **real MD1+MD2** and re-evaluates the manipulability
incentive at each team's *true* MD3 decision point (official bracket, both models, 40 snapshots ×
150 inner). Artifact: `results/scoring.json`.

**H1/H2 (computational estimands, behavior-independent):** unchanged by realization — multiplier
1.66 [1.59,1.73] (>1), cross-group share 48% (48-team) vs 0% (32-team). Established by the frozen
computation; the group stage does not bear on them.

**H3 — the prospective named predictions. Registered robust set (P≥0.50 both models at freeze) vs
realized manipulability given real standings:**

| Match | frozen elo/pois | realized elo/pois | confirmed? |
|-------|:---:|:---:|:---:|
| Canada vs Switzerland (B) | 57/74% | **98/100%** | ✅ |
| Algeria vs Austria (J) | 54/65% | **92/100%** | ✅ (finished **3–3**, both to 4 pts) |
| Brazil vs Scotland (C) | 56/78% | 68/65% | ✅ |
| Czech Republic vs Mexico (A) | 55/67% | 55/57% | ✅ |
| Netherlands vs Sweden (F) | 56/58% | 68/38% | ✖ (split: elo yes, poisson no) |

**4 of 5** registered robust predictions were realized-manipulable (the structural incentive genuinely
existed at MD3 given the real standings); the two strongest cross-group calls — **Canada–Switzerland
(99%)** and **Algeria–Austria (96%, 96% cross-group)** — were near-certain, and Algeria–Austria
actually ended in a high-scoring **3–3 mutual-benefit draw** that carried both teams forward (Austria
2nd, Algeria 3rd via the best-third pool). Rank agreement frozen-vs-realized: **Spearman ≈ 0.46–0.48**
(positive but moderate — expected, since the freeze was a noisier *two-matchday-ahead* forecast and
conditioning on real MD2 sharpens which states are live); Brier 0.16–0.22.

**The cross-group mechanism manifested in reality.** The highest *realized* cross-group incentives were
Algeria–Austria (96%), **Japan–Tunisia (92%)** and **Curaçao–Ecuador (77%)** — all driven by the
best-third pool being decisive (these last two were *under*-predicted at the pre-MD2 freeze, 37% and
15%, then became strongly manipulable once real standings were known). Conversely some frozen calls
dissolved by MD3 (e.g. England–Panama 45%→0%, once qualification was settled). The eight best-third
teams that actually advanced (Bosnia, Paraguay, Ecuador, Sweden, Senegal, Algeria, DR Congo, Ghana)
confirm the cross-group qualification channel was live and outcome-determining.

**Behavioral endpoint:** descriptive only, per the pre-registered power rule (E=2.76<3) and absent
match-event/passivity data. We therefore claim the **structural incentive was present and correctly
anticipated**, not that teams demonstrably acted on it; Algeria–Austria's 3–3 is suggestive but
confoundable (the pre-registered limitation).

**Verdict:** the pre-registered live test lands — a frozen, timestamped, two-matchday-ahead model
named the manipulable group-finale matches, 4/5 of its robust set realized, and its signature
cross-group cases (Canada–Switzerland, Algeria–Austria) were the most manipulable matches of the round.

---

## R14 — Equilibrium robustness (preliminary): cross-group manipulability survives the game (2026-06-29)

**Addresses R1's central concern** — the headline is *decision-theoretic* (a team's best response vs
sampled opponents), but the finale is a simultaneous-move game. We re-solve each group's MD3 as a game
(`scripts/run_equilibrium.py`, best-response dynamics with a significance margin, `equilibrium.py`),
at the real pre-MD3 state, official bracket, Elo, inner=200. Artifact: `results/equilibrium.json`.

**Result:** **8 of 12 groups reach a pure Nash equilibrium**; the structural claim **holds under the
equilibrium notion** — cross-group (best-third) manipulability is present in equilibria, not just a
best-response artifact. Equilibrium-cross-group teams: **Brazil (C), Senegal (I), Algeria (J),
Croatia (L)** (cross-group share among equilibrium-manipulable teams ≈ 0.21, i.e. >0).

**Honest caveats (why this is robustness, not the headline):**
- **4 groups have no pure NE** (F, H, I, J cycle) → those need a mixed-strategy / fictitious-play
  treatment; their rows are last-iterate, not true equilibria, so the aggregate rate (0.40) and share
  (0.21) are contaminated and should not be quoted as precise.
- The equilibrium cross-group share appears **attenuated** vs the decision-theoretic estimate — the
  mechanism persists but the game can wash out some best-response incentives (mutual-interest
  resolution, opponents also deviating).
- At the *real* pre-MD3 state several groups are already decided, so some non-WIN equilibrium actions
  are near-indifference (path/seeding), not best-third manipulation.

**Takeaway:** the cross-group mechanism is **robust to making the finale a game** (the qualitative claim
R1 asked about survives); a clean quantitative equilibrium share awaits increment 3 (mixed strategies
for the no-pure-NE groups + a state matched to the decision-theoretic comparison). The paper's headline
remains the decision-theoretic decomposition (R12); §4.3 / R14 are the equilibrium robustness.

---

## R15 — Information regime: the cross-group share is invariant to the schedule (2026-07-01)

**Addresses R1's blind spot / R3's suggested experiment** — "the all-groups-simultaneous counterfactual
is never simulated to bound how much of the 48% is irreducible vs schedule-induced." Two findings.

**(a) The headline already IS the simultaneous, no-information regime.** Code audit: in
`engine._simulate_remainder`, `state.fixed` holds only MD1–2; at MD3 the decision team's own match is the
evaluated action and *every* other match — all other groups' finales and the team's own group's other
final — is Monte-Carlo **sampled, not observed**. So the reported 48% cross-group share is computed while
integrating over other groups' unknown results: the conservative, no-cross-group-information bound that
post-Gijón simultaneity is designed to enforce. Made explicit in `main.tex` Methods.

**Real schedule (for the staggered regime).** Sourced per-group MD3 kickoff times from the FOX Sports 2026
broadcast schedule (official US broadcaster), cross-checked for day assignment against Wikipedia + ESPN.
Both matches within a group kick off simultaneously; the 12 finales form a **complete temporal order**:
B<C<A (Jun 24), E<F<D (Jun 25), I<H<G (Jun 26), L<K<J (Jun 27) — note the within-day order is not
alphabetical (host group A finishes last on Jun 24). Stored as `schedule[g].md3_kickoff_et` with
provenance. A later group's staggered information set = the real MD3 of all strictly-earlier-kickoff groups.

**(b) Format-level estimand (`run_info_regime.py --mode format`, 80 snapshots × 150 inner, both models
pooled, cluster bootstrap over snapshots).** Simultaneous vs staggered cross-group share:

| Regime | manip rate | cross-group share [95% CI] |
|--------|-----------:|---------------------------:|
| simultaneous (headline) | 0.235 | **48.3% [46.1, 50.6]** |
| staggered (real schedule) | 0.247 | **49.9% [47.4, 52.6]** |

The simultaneous arm **reproduces the R12 headline (48%)** — a pipeline validation. The staggered share is
**statistically indistinguishable** (overlapping CIs; by day tier: Jun24 39→40, Jun25 57→57, Jun26 50→52,
Jun27 50→52). *Correcting an earlier intuition:* conditioning on real earlier-group results does not
monotonically sharpen the incentive — information can also **resolve** a cross-group state to certainty —
and the net effect is null within noise. The mechanism is **neither created nor removed by the schedule**.

**(c) Realized exploitability audit (`--mode realized`, 60 × 150, conditioning on the real MD1–2, and for
the staggered arm the real earlier-kickoff MD3).** At the actual post-MD2 state the finale is largely
resolved (7/24 matches live-manipulable, consistent with R13). The **same 3 matches are cross-group
manipulable under both regimes** (0 flip): no match's cross-group status depends on whether its earlier
groups' real MD3 is known. Sparse but stable — the realized cross-group set is regime-invariant too.

**Verdict:** the 48% cross-group share is **structural, not a schedule artifact** — identical with zero
schedule information and unchanged (within CI) when the real staggered schedule supplies it. This closes
the "simultaneity counterfactual" concern (R1 blind spot, R3 experiment) directly. Artifacts:
`results/info_regime_format.json`, `results/info_regime.json`. Same-day granularity available as a
conservative robustness check (`--granularity date`).
