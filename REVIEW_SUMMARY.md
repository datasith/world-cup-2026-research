# Reviewer panel — consolidated summary

**Run:** `results/reviews/20260617_103130/` · **Date:** 2026-06-17
**Panel:** R1 Theorist (`claude-opus-4-8`) · R2 Domain Skeptic (`gpt-5.5`) · R3 Methodologist (`gemini-3.5-flash`)

## Verdicts & scores (1–5)

| Reviewer | Rec | Novelty | Rigor | Signif. | Clarity | Repro |
|----------|-----|:---:|:---:|:---:|:---:|:---:|
| R1 Theorist | major revision | 3 | **2** | 3 | 3 | 4 |
| R2 Domain Skeptic | **reject** | 2 | **1** | 2 | 2 | 2 |
| R3 Methodologist | major revision | 4 | **2** | 4 | 3 | 4 |

**Shared read:** the *idea* is strong and timely (R3 "outstanding" framing; R1 "genuinely disciplined" pre-reg) but the **execution under-delivers on the theory and the causal/statistical rigor**, and the **manuscript itself is still TODO placeholders**. Rigor is the universal weak point. R2 (the domain referee) is harshest: in current form it's "a project scaffold," not a submittable paper.

---

## Consensus findings (flagged by ≥2 reviewers — highest priority)

### C1. The central objects (`V_adv`, "manipulable state", action space) are under-specified — **R1 (critical), R2 (critical)**
Every reported number (ρ, multiplier, cross-group share, named P(manip)) is a function of `V_adv` and the action space, but `THEORY.md §6` lists "operationalize V_adv" and "define the action space" as *open*. There's also a definitional clash: `RESULTS.md R1 caveat 5` says Δ = "expected knockout rounds won," while `THEORY.md §2` says "probability-weighted advancement + bracket-path strength" — different functionals.
**Fix:** give one closed-form `V_adv` (terminal bracket-node values + path weighting + action family), use it everywhere, and report sensitivity to ≥2 specifications (rounds-won vs win-prob-weighted).

### C2. The "trilemma" is a conjecture but the **title asserts it as fact** — **R1 (critical), R2 (critical)**
`THEORY.md §4` labels it *Conjecture* with an undefined breadth threshold (`§6` open); the title says expansion "breaks the strategyproofness of the group stage." R1 notes it isn't even obviously an impossibility as stated.
**Fix (R1's recommended path):** prove the *restricted, provable* theorem — "any advancement rule whose advancement of *t* depends on a comparison with teams outside *t*'s simultaneously-played match admits a manipulable state simultaneity cannot remove; M₄₈ satisfies the antecedent, M₃₂ does not." Then either keep the trilemma as an explicitly labeled conjecture or soften the title to a measured claim.

### C3. The expansion multiplier is **not causally identified** — **R1 (major), R2 (major)**
The 1.69 mixes ≥4 changes at once: best-third rule + 12-group structure + qualification math + (R3 arm) real-draw-48 vs synthetic-matched-32.
**Fix:** factorial decomposition — add a within-48 arm toggling **only** the best-third rule (12 groups, top-2 vs top-2+best-third), and match the draw-generation process across formats. Report what fraction of the multiplier the cross-group rule specifically explains. Treat the official-draw number as a case study, not the causal effect.

### C4. Pre-registration integrity / leakage — **R1 (blind spot), R2 (critical), R3 (inconsistency)**
R1–R7 contain extensive exploratory runs, named predictions, thresholds, and even a CI-method change *before* the OSF freeze commit/DOI exist; H1/H2 are "confirmed by a frozen computation," and H2 is partly tautological (M₃₂ has no best-third pool by construction).
**Fix:** describe this honestly as a *prospective analysis plan informed by exploratory simulation*, not a pure pre-registration. Freeze code+data+predictions+scoring on OSF with immutable hashes **before MD3**; give the frozen post-MD2 prediction set a **new artifact name**; relabel H1/H2 as computational *estimands*, reserve "confirmatory" for the prospective H3.

### C5. FIFA rules fidelity, esp. **Round-of-32 third-place bracket assignment** — **R1 (blind spot), R2 (critical), R3 (blind spot)**
Best-third teams are mapped into specific bracket slots by a fixed lookup table; a team's desired result can depend on *bracket slot*, not just qualifying. Tie-breaks (GD, GF, head-to-head, fair-play points, drawing of lots) must match the regulations exactly.
**Fix:** add a regulation-level appendix + unit tests reproducing known cases; implement the official R32 third-place table; separate "qualification" incentives from "opponent-avoidance / bracket-path" incentives in the results.

### C6. Information sets / temporal asymmetry — **R2 (major), R3 (blind spot)**
The 12 groups don't all kick off simultaneously; later groups know the exact third-place thresholds, earlier ones don't. The static pre-match model can misclassify incentives, and the "simultaneity-irreducible" claim needs the *actual* schedule.
**Fix:** model explicit information regimes (ex-ante no live info; completed-earlier-groups; full live; all-groups-simultaneous counterfactual) using the real MD3 kickoff windows.

### C7. Strength-model calibration — **R2 (major), R3 (major)**
Elo→Poisson `base_goals=1.35, spread=0.95` are hand-tuned; the Bayesian Poisson may omit the **Dixon–Coles low-score correlation (ρ)**, which would underestimate draws — and draws drive group math/tie-breaks. Posterior uncertainty isn't propagated (point estimates only).
**Fix:** report out-of-sample calibration (Brier/log-loss/RPS, exact-score, GD, draw cells), benchmark vs market odds, implement or justify Dixon–Coles ρ, and propagate posterior parameter uncertainty through the simulator.

### C8. Behavioral (H3) endpoint is underpowered — **R1, R2, R3 (all)**
R3's sharp point: the "own tournament baseline" for passivity proxies is **N=2 matches** (MD1+MD2) — statistically meaningless. Plus confounds (rotation, score state, fatigue) and no power calc.
**Fix:** historical/team-type baseline for the null; matched-control design (similar score/time states without manipulation incentive); a pre-registered composite passivity index with FDR correction; and a **power / minimum-detectable-effect** calc. Frame as descriptive/illustrative unless powered.

### C9. Missing prior art — **R1, R2, R3 (all) — strong consensus**
Must engage, not just name: **Dagaev & Sonin (2018) "Winning by losing"**; **Csató, *Tournament Design* (2021)**; **Pauly (2014)** round-robin strategyproofness; **Vong (2017)** tournament manipulation; **Kendall & Lenten (2017)** "when sports rules go awry"; **Guyon** (WC draw/format, groups-of-three); **Csató & Gyimesi (2025)** (engage directly, not just cite); Gibbard–Satterthwaite + Duggan–Schwartz lineage. *(Reviewers flagged uncertainty on exact titles/years — verify before citing.)*

### C10. The manuscript is essentially empty — **R2 (critical)**
`paper/main.tex` is all `\todo{}`. R2 (correctly) won't evaluate a paper of placeholders.
**Fix:** this is the gating item for any real submission — write the actual Methods/Results/Discussion.

---

## Notable single-reviewer points

- **R1:** "the manipulable state is a single-team decision problem in what is actually a *simultaneous-move game*" — is it a best response vs a fixed opponent model (decision-theoretic) or a Nash equilibrium property? The simulator must declare which; the two give different cross-group shares.
- **R1 & R2:** the "32-team has *zero* irreducible manipulability" framing is overstated — **Gijón-style collusive scoreline targeting between two teams playing each other survives simultaneous kickoffs** even in the 32-team format. Qualify the dichotomy.
- **R3 (critical): ✅ addressed** — Monte-Carlo budget too small. Convergence study done (R8): multiplier noisy below ~40 snapshots, stable from ~80, settled at N=400; budget raised to ≥400 with a convergence plot (`results/convergence.png`).
- **R3 (critical) & inconsistency:** the **ML calibration layer** promised in `DESIGN.md §4` / `main.tex` Methods is absent from the pre-reg and results → looks like a dropped/selective plan. Either integrate it fully or remove all references.
- **R2 (verify):** R4 says "16 real MD1 results" — a 48-team MD1 is **24 matches**. Either a data/labeling bug or MD1 was only partially played; must be clarified (it's central to the live predictions). **→ worth verifying against `data/draw_2026.json` now.**
- **R3 (inconsistency):** PREREGISTRATION §3 states snapshots ≥ 60, but R7's corrected run used 30 — violates the stated minimum.

---

## AI-authorship detection (the prose-cleanup task)

Likelihoods: **R1 0.50 (med)** · **R2 0.78 (med)** · **R3 0.85 (high)**. All three converged on the same culprits — and crucially, the tells are in the **planning docs (`DESIGN.md`, `RESULTS.md`), not the (empty) manuscript**. The most-flagged, must-fix phrases:

| Where | Flagged phrase | Why it reads as AI | Fix |
|---|---|---|---|
| DESIGN.md | "This is the **flagship-best angle**: general theorem + crisp number + …" | stacked buzzwords / self-evaluation | state the contribution plainly |
| DESIGN.md | "the **flagship-shaped story**" / "This is the **credibility centerpiece**" | meta-writing about *looking* publishable | delete or convert to technical statement |
| **DESIGN.md** | "**The user's instinct is right** — this is crowded…" | **leaks the chat-assistant origin** | delete entirely |
| RESULTS.md | "This **lifts the live test from 'an Elo forecast'** to a model-family-stable prediction" | rhetorical uplift, overstates two related Poisson models | "rank order is similar under Elo and Poisson, so the prediction isn't Elo-specific" |
| RESULTS.md | "the cross-group cases (e.g. Brazil–Scotland) are the novel mechanism" | repeats the slogan without showing the rule path | replace with the concrete qualification-probability path |

**Action:** these are quick, high-value edits — strip the strategic/meta framing from `DESIGN.md` and `RESULTS.md`, especially the chat-leak line, and replace rhetorical sentences with concrete technical ones. (The manuscript prose itself doesn't exist yet, so real AI-tell cleanup happens as it's written.)

---

## Prioritized action plan

**Already done (this session):** cluster-bootstrap CIs (C-partial), model-family robustness (R5), margin sensitivity (R6).

**Do now (cheap, high-value):**
1. ✅ **Done** — stripped AI-tells / chat-leak from `DESIGN.md` + `RESULTS.md`.
2. ✅ **Done** — verified: only **16 of 24** MD1 matches are recorded (MD1 incomplete); wording
   corrected in `RESULTS.md` (R4/R5) and the `r4_named.json` artifact meta. Not a bug, but the
   prior "16 real MD1 results" phrasing falsely implied a complete matchday.
3. ✅ **Done** — removed the promised gradient-boosted/neural "ML layer" from `DESIGN.md §4` and
   `paper/main.tex` Methods (kept the contrasting reference to ML-prediction work); docs now match
   the Elo + Bayesian-Poisson implementation.
4. ✅ **Done** — convergence study (RESULTS.md R8, `results/convergence.png`): multiplier stabilizes
   by N≈80, settles at **1.64 [1.58, 1.71]** at N=400, CI excludes 1.0 at every budget. Prereg §3
   budget raised to **≥400 snapshots** (data-justified), §4 CI method corrected to cluster bootstrap,
   amendment logged in §9. Resolves the ≥60-vs-30 inconsistency **and** R3's Monte-Carlo-budget
   critique (see single-reviewer points).

**Do before the OSF freeze (~June 23–24):**
5. Scale Monte-Carlo to ≥500 snapshots + convergence plot (C: R3).
6. Honest pre-reg reframing + new frozen-artifact name; relabel H1/H2 as estimands (C4).
7. Fix the N=2 passivity baseline + add an H3 power calculation (C8).

**Do for the paper to be theory-credible (the hard core):**
8. Pin `V_adv` with one definition + sensitivity (C1).
9. Prove the restricted cross-group impossibility proposition; relabel/soften the trilemma + title (C2).
10. Factorial decomposition isolating the best-third rule (C3).
11. Implement + test exact FIFA R32 bracket assignment and tie-breaks (C5); add information-regime modeling (C6).
12. Model calibration (Dixon–Coles ρ, posterior propagation, calibration metrics) (C7).
13. Engage the prior-art literature directly (C9).
14. Write the actual manuscript (C10).
