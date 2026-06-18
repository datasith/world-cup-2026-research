# Pre-registration — manipulability of the 48-team World Cup group finale

**Study:** *The price of expansion is manipulability: enlarging the FIFA World Cup to
48 teams breaks the strategyproofness of the group stage.*
**Authors:** datasith et al. (California Institute of Technology)
**Protocol drafted (frozen, pre-data):** 2026-06-16 — **before Matchday 2 (MD2) is played.**
**Freeze commit:** `<filled at OSF submission>` · **OSF DOI:** `<filled at OSF submission>`
**Code:** https://github.com/datasith/world-cup-2026

> The scientific value of this document is that it fixes the model, the predictions, and
> the **scoring rule** *before* the outcomes exist. It is written on 2026-06-16, before MD2
> (starts ~2026-06-18) and the group finale MD3 (~2026-06-24). Nothing below may be changed
> after data arrive except via the dated amendment log in §9.

---

## 1. Background and aim

The 48-team format advances, per group, the top two teams **plus the 8 best third-placed
teams** to a Round of 32. A third-placed team's required final-matchday result therefore
depends on the standings of **other groups** — a *cross-group* dependency that within-group
**simultaneous kickoffs** (FIFA's post-Gijón 1982 fix) structurally **cannot** remove. We
test whether expansion raises the rate and stakes of *manipulable match-states* — states
where a team's advancement-optimal action is **not** to maximize its chance of winning the
match — and we issue named, falsifiable predictions for the 2026 group finale. Formal
definitions: [`THEORY.md`](THEORY.md).

## 2. Hypotheses (directional, fixed in advance)

- **H1 (expansion multiplier).** The final-matchday manipulability rate is higher under the
  48-team format than the 32-team format: ρ(M₄₈) / ρ(M₃₂) > 1.
- **H2 (simultaneity-irreducible mechanism).** The cross-group share of manipulable states
  is > 0 under M₄₈ and = 0 under M₃₂. This is the structural novelty; it is the share that
  simultaneous kickoffs cannot eliminate.
- **H3 (named live predictions).** Among the 24 MD3 matches actually played in 2026, the
  matches we rank highest for P(manipulable) (§5) contain teams that, at MD3 kickoff, face a
  manipulation incentive; the ranking is correlated with realized incentive structure.

H1 and H2 are the **confirmatory core** (computed from the format + draw + strength model;
they do **not** depend on how teams behave). H3 adds named, in-tournament predictions.

## 3. Strength model and simulator (locked)

- **Primary strength model:** time-varying Elo, full-history fit (`src/wc2026/fit_elo.py`),
  Elo→Poisson scoreline sampler (`EloSampler`, base_goals=1.35, spread=0.95).
- **Robustness model (co-primary for H3 stability):** hierarchical Bayesian Poisson
  (`src/wc2026/bayesian.py`, non-centered, 4 chains), `PoissonSampler`. *Calibration note (C7):*
  the current Poisson is **independent** (no Dixon–Coles low-score ρ), which underestimates draw
  probabilities; both models' goal parameters are not yet fit to goal-level data. We commit to
  reporting out-of-sample calibration (Brier / log-loss / RPS, plus draw-cell calibration) in the
  manuscript and to checking that the named predictions are unchanged under a ρ-corrected refit;
  this is a stated limitation, and the freeze locks the models *as implemented*.
- **Knockout bracket:** the **official 2026 R32→final bracket** (`src/wc2026/bracket.py`,
  `--bracket official`), not the strength-seeded stand-in, so V_adv reflects the real bracket
  geometry (this is load-bearing for the cross-group/path mechanism; THEORY §4.1).
- **Simulator:** Monte-Carlo over the bracket; format and draw are the swapped variables.
  Official 2026 draw: `data/draw_2026.json`. Official matchday schedule used for MD ordering.
  *Information regime (C6):* a team's MD3 decision is evaluated at its **pre-match information set**
  — cross-group results already completed under the official schedule are known; the simultaneous
  same-group match is not. The static pre-match regime is the registered one; sensitivity to a
  full-live-information regime is a stated limitation (the schedule's temporal asymmetry across
  groups is precisely why cross-group dependencies are observable and not removed by within-group
  simultaneity).
- **Determinism:** all runs use fixed seeds (default `--seed 20260616`); the frozen artifact
  records its seed, snapshot, inner, and margin parameters in its `meta` block.
- **Monte-Carlo budget at freeze:** snapshots ≥ 400, inner ≥ 150 — convergence-justified: the
  expansion-multiplier point estimate is flat to ±0.03 and its 95% CI half-width < 0.07 by 400
  snapshots (RESULTS.md R8; `results/convergence.png`). Raise further if a named match's P(manip)
  95% cluster-bootstrap CI half-width exceeds 0.05. *(Amended 2026-06-17 from "≥ 60"; see §9.)*

## 4. Estimands and analysis plan

1. **ρ(M):** P[final-matchday state is manipulable for some team], per format.
2. **Cross-group share:** fraction of manipulable states whose dependency routes through the
   best-third pool (measured, not assumed — see RESULTS.md R2 vs R1).
3. **Expansion multiplier:** ρ(M₄₈)/ρ(M₃₂), with 95% CI by **cluster bootstrap over snapshots**
   (states within a snapshot are correlated; see RESULTS.md R7).
4. **Per-match / per-team P(manipulable) and P(cross-group)** for the real 2026 MD3.

**Robustness (pre-committed):** every headline number is reported under **both** the Elo and
the Bayesian-Poisson model. A named MD3 prediction (§5) is labeled **robust** only if it
ranks in the top tier under *both* models; the confirmatory test of H3 uses the robust set.

**Sensitivity (pre-committed):** the manipulability margin/threshold (`--margin`, the q3
noise band) is reported at {0.03, 0.05, 0.08}; conclusions must not hinge on one value.

## 5. The predictions (frozen artifact)

The named MD3 predictions are the ranked `matches` and `teams` arrays in the frozen artifact
`results/r4_named.json` (regenerated and re-frozen post-MD2; see §6). Each carries
`p_manipulable` and `p_cross_group`. The **registered prediction set** is, at freeze time:

- **Match-level:** the ranking of all 24 MD3 matches by P(manipulable), and the named subset
  with P(manipulable) ≥ 0.50 under both models (the *robust* set).
- **Team-level:** the named teams with P(cross_group) ≥ 0.20 — the simultaneity-proof cases,
  which are the mechanism's signature and the sharpest novelty.

Early projections in RESULTS.md R4/R11 are preliminary; the **registered set is the artifact
produced by the freeze run (§6)** conditioned on all results available at freeze time.

## 6. Freeze timing and procedure

- **Window (amended 2026-06-17, §9):** **after Matchday 1, before Matchday 2** (~2026-06-17/18).
  This trades the lowest-variance freeze (post-MD2) for **maximal lead time** — MD2 *and* MD3 are
  unobserved at freeze, so the named predictions are a genuinely prospective two-matchday-ahead
  forecast (a stronger anti-leakage guarantee, at the cost of wider intervals). The simulator
  conditions on every MD1 result recorded in `data/draw_2026.json` at freeze time and simulates all
  unplayed MD1/MD2 continuations; if MD1 is not fully recorded, that is disclosed (RESULTS R4: 16/24).
- **Procedure:** (a) ensure `data/draw_2026.json` holds all available MD1 results; (b) run the
  locked command under both models; (c) commit the artifact + this protocol; (d) push and create the
  OSF registration referencing the freeze commit hash; (e) record hash + DOI in §0 header.
- **Locked command:**
  `uv run python scripts/run_r4_named.py --bracket official --model {elo,poisson} --snapshots 400 --inner 150 --margin 0.05`

## 7. Scoring rule (fixed before data)

**Primary (confirmatory, behavior-independent).** H1 confirmed iff the multiplier's 95% CI
excludes 1.0 with point estimate > 1. H2 confirmed iff cross-group share > 0 for M₄₈ (and is
identically 0 for M₃₂ by construction). These are decided by the frozen computation and the
real draw/results; **no team behavior is required.** This is the rigorous core of the paper.

**Secondary (corroborating, behavior-based, H3).** For each robust named match, classify the
implicated team's MD3 performance as *consistent* / *inconsistent* / *non-diagnostic* with the
manipulation-optimal action, using **pre-specified passivity proxies**: in-play win-probability
volatility, shot rate, and pressing intensity (PPDA), evaluated **only once the team's
advancement-optimal target is non-winning and the match is live at the decision point.**

*Baseline (fixed; C8 — replaces the earlier "own tournament baseline").* A team's MD1+MD2 in this
tournament is only **N=2 matches**, far too few to define a null. Instead each proxy is standardized
against a **historical/strength-matched baseline**: the distribution of that proxy for teams of
comparable strength (Elo bin) in competitive internationals over the prior 2–3 years, with opponent
strength and game-state as covariates. The test statistic is a single **pre-registered composite
passivity index** (mean of the standardized proxies); match-level tests use **Benjamini–Hochberg FDR
control** across the robust set.

*Power (fixed; C8).* The behavioral test is powered only if enough manipulable MD3 matches are
actually *realized*. We pre-compute, from the frozen artifact, the **expected number of realized
robust manipulable matches** $E=\sum_{m\in\text{robust}}P(\text{manip}_m)$ and its distribution over
continuations; **if $E<3$ the behavioral endpoint is declared underpowered and reported as
descriptive/illustrative only** (the primary, behavior-independent endpoint carries the paper). The
realized $E$ from the freeze run is recorded in RESULTS R11.

Report the count of confirmed vs. falsified named predictions and a rank correlation (Spearman)
between P(manipulable) and an ex-post incentive indicator. The secondary endpoint is **corroborating,
explicitly confoundable** (§8) and does not gate the main claim. A single pre-registered, then
realized, manipulation event is the headline **illustration**, not the test.

## 8. Confounds and limitations (declared in advance)

- Passivity is confoundable by fatigue, squad rotation, injuries, and tactics; hence the
  behavior endpoint is secondary and the manipulable-state *count* is primary.
- Strength-model error propagates to projected standings; mitigated by the dual-model
  robustness rule (§4) and by conditioning on real results at freeze (§6).
- Best-third tie-breaks: group ranking uses points, GD, GF, head-to-head, then a seeded coin
  (`formats.py`); the R32 third-place→slot assignment uses the official candidate sets
  (`bracket.py`). **Fair-play / disciplinary tie-breaks are not simulated** (cards unmodelled) —
  a stated limitation; any deviation discovered is logged in §9, not silently corrected.
- Information regime is the static pre-match set (C6, §3); live in-play dynamics are not modelled.
- Strength models: independent Poisson (no Dixon–Coles ρ) and hand-set Elo→goals mapping; calibration
  to be reported and the named set re-checked under a ρ-corrected refit (C7, §3).
- Monte-Carlo noise: reported with cluster-bootstrap CIs; budget raised if CIs are too wide (§3).

## 9. Amendment log

Any change after 2026-06-16 is dated and justified here; pre-data text above is immutable.

- **2026-06-17:** §3 Monte-Carlo budget raised from "snapshots ≥ 60" to "≥ 400" and the §4
  multiplier CI method changed from "bootstrap over states" to "cluster bootstrap over snapshots."
  Justification: a convergence study (RESULTS.md R8) showed low-snapshot estimates are noisy and the
  per-state bootstrap mis-specifies the resampling unit. Both changes are pre-MD2 (no MD2/MD3 outcome
  data exist yet) and only make the analysis more conservative; no hypothesis or prediction changed.
- **2026-06-17 (reviewer-driven, all pre-MD2):** (a) §6 freeze window moved to **after MD1, before
  MD2** for maximal lead time (predictions become a two-matchday-ahead forecast). (b) §3 knockout
  switched to the **official R32→final bracket** (`bracket.py`) from the strength-seeded stand-in.
  (c) §7 passivity baseline changed from the N=2 "own tournament" baseline to a **historical
  strength-matched** baseline + composite index + BH-FDR, and a **power rule** added ($E<3$ ⇒
  behavioral endpoint descriptive only). (d) §3 calibration (Dixon–Coles ρ) and information-regime
  limitations declared. None of these change the hypotheses or the prediction *targets*; they make the
  geometry exact and the scoring more conservative, before any MD2/MD3 data exist.
