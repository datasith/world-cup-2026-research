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
  (Dixon–Coles style, `src/wc2026/bayesian.py`), `PoissonSampler`.
- **Simulator:** Monte-Carlo over the bracket; format and draw are the swapped variables.
  Official 2026 draw: `data/draw_2026.json`. Official matchday schedule used for MD ordering.
- **Determinism:** all runs use fixed seeds (default `--seed 20260616`); the frozen artifact
  records its seed, snapshot, inner, and margin parameters in its `meta` block.
- **Monte-Carlo budget at freeze:** snapshots ≥ 60, inner ≥ 150 (raise if a named match's
  P(manip) 95% bootstrap CI half-width exceeds 0.05).

## 4. Estimands and analysis plan

1. **ρ(M):** P[final-matchday state is manipulable for some team], per format.
2. **Cross-group share:** fraction of manipulable states whose dependency routes through the
   best-third pool (measured, not assumed — see RESULTS.md R2 vs R1).
3. **Expansion multiplier:** ρ(M₄₈)/ρ(M₃₂), with 95% CI by bootstrap over states.
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

The early (pre-MD2) projection recorded in RESULTS.md R4 is **not** the registered set; it is
disclosed as a preliminary projection. The registered set is the post-MD2 re-run (§6), which
conditions on real MD1+MD2 results so that only MD3 outcomes remain uncertain.

## 6. Freeze timing and procedure

- **Window:** after MD2 completes and before MD3 kicks off (~2026-06-23/24). This is the
  lowest-variance freeze — all of MD1 and MD2 are then real, only MD3 is uncertain.
- **Procedure:** (a) update `data/draw_2026.json` with real MD2 results; (b) run the locked
  command under both models; (c) commit the artifact + this protocol; (d) push and create the
  OSF registration referencing the freeze commit hash; (e) record hash + DOI in §0 header.
- **Locked command:**
  `uv run python scripts/run_r4_named.py --model {elo,poisson} --snapshots 60 --inner 150 --margin 0.05`

## 7. Scoring rule (fixed before data)

**Primary (confirmatory, behavior-independent).** H1 confirmed iff the multiplier's 95% CI
excludes 1.0 with point estimate > 1. H2 confirmed iff cross-group share > 0 for M₄₈ (and is
identically 0 for M₃₂ by construction). These are decided by the frozen computation and the
real draw/results; **no team behavior is required.** This is the rigorous core of the paper.

**Secondary (corroborating, behavior-based, H3).** For each robust named match, classify the
implicated team's MD3 performance as *consistent* / *inconsistent* / *non-diagnostic* with the
manipulation-optimal action, using **pre-specified passivity proxies**: in-play win-probability
volatility, shot rate, and pressing intensity (PPDA) relative to that team's own tournament
baseline, evaluated **only once the team's advancement-optimal target is non-winning and the
match is live at the decision point.** Report the count of confirmed vs. falsified named
predictions and a rank correlation (Spearman) between P(manipulable) and an ex-post incentive
indicator. The secondary endpoint is reported as **corroborating evidence, explicitly
confoundable** (see §8) — it does not gate the paper's main claim.

**A single pre-registered, then realized, manipulation event** (a top-ranked team visibly
playing for a non-winning result that its frozen incentive predicted) is the headline
illustration, framed as illustration, not as the test.

## 8. Confounds and limitations (declared in advance)

- Passivity is confoundable by fatigue, squad rotation, injuries, and tactics; hence the
  behavior endpoint is secondary and the manipulable-state *count* is primary.
- Strength-model error propagates to projected standings; mitigated by the dual-model
  robustness rule (§4) and by conditioning on real results at freeze (§6).
- Best-third tie-breaks and FIFA's exact disciplinary/lots rules are implemented as specified
  in `formats.py`; any deviation discovered is logged in §9, not silently corrected.
- Monte-Carlo noise: reported with bootstrap CIs; budget raised if CIs are too wide (§3).

## 9. Amendment log

Any change after 2026-06-16 is dated and justified here; pre-data text above is immutable.

- _(none yet)_
