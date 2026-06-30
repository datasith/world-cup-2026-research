# World Cup 2026 — Research Design Plan

**Title:** *Game's gone: pre-registered manipulability in the 2026 World Cup* (subtitle: *the
best-third rule, not the larger field, increases group-stage manipulability*). Softened from
"breaks the strategyproofness" per reviewer R1 — we prove a restricted cross-group existence result,
THEORY §4.1, and measure the increase, R9; we do not prove a general impossibility.

Lead result is the game-theoretic **manipulability / strategyproofness** analysis (angle #4),
instrumented by the entropy/predictability machinery and tested live this month. Formal
definitions live in [`THEORY.md`](THEORY.md).

Status: scaffolding / idea selection. Last updated 2026-06-16.

---

## 1. The honest publishing landscape (literature scan, 2026-06-16)

Summary of the relevant literature, to position the contribution. Nature and Science reject ~92%
of submissions and rarely publish a sports analysis unless it answers a question of broad
scientific significance, so the framing has to clear that bar.

**What already exists:**

- **Tournament design / competitive balance** lives in *operations research* journals, not the
  flagships. The closest competitor is Csató & Gyimesi, *"Increasing competitiveness by imbalanced
  groups: the example of the 48-team FIFA World Cup"* (European J. Operational Research, 2025;
  arXiv:2502.08565). They use Elo + Monte Carlo simulation to argue imbalanced groups raise
  competitiveness. **This is the paper we must differentiate from.**
- **ML match prediction** is heavily worked: Springer *Machine Learning*, Frontiers, Applied
  Sciences, plus the recurring "Soccer Prediction Challenge." Accuracies of 63–87% are routinely
  reported. A *pure* "we predicted matches with an ML model" paper has near-zero flagship novelty.
- **Nature-*family* (not flagship)** has published football: TacticAI (Nat. Communications, 2024,
  geometric deep learning on corner kicks); spatial structure of teams (Sci. Reports, 2025);
  competitive balance in 10M online games (Sci. Reports). These are the realistic homes for strong
  work that isn't broad enough for flagship Nature/Science.
- **Sustainability** is saturated *and journalistic*: Greenly (7.8 Mt CO2e), New Weather Institute
  (~9 Mt), "most polluting ever." Mostly industry reports and press, not peer-reviewed science —
  crowded and not a flagship path; not pursued.

**The gap:** No one has treated the 2026 expansion as a *prospective natural experiment* on a
complex competitive system and used it to test *generalizable* theory about how the structure of a
competition (not the competitors) controls fairness, predictability, and the rate of upsets. That
framing — competition design as a controllable parameter of a complex adaptive system — is what can
travel beyond football into a flagship/PNAS/Nature Human Behaviour readership.

## 2. Target-journal realism (recommendation)

| Tier | Venue | Realistic if... |
|------|-------|-----------------|
| Reach | **Nature / Science** | We deliver a genuinely generalizable result + a striking, pre-registered prediction that the live tournament confirms. Treat as aspirational. |
| Strong | **Nature Human Behaviour, PNAS, Nature Communications** | Rigorous natural-experiment design + novel metric. This is the honest primary target. |
| Solid | **Scientific Reports, Royal Society Open Science, EPJ Data Science** | Backstop; strong analysis even without flagship-level generality. |

Recommendation: **design for Nature Human Behaviour / PNAS as the primary target, write the abstract
so it *could* go to Nature first.** A pre-registered live prediction is the single highest-leverage
thing that distinguishes us from every retrospective paper.

## 3. Candidate angles (catchy + novel), ranked

### ⭐ #4 (LEAD). "The price of expansion is manipulability" — strategyproofness of the format
Game-theoretic / mechanism-design lead. The 48-team format advances the **8 best third-placed
teams**, making a team's required group-finale result depend on **other groups** — a *cross-group*
dependency that within-group simultaneous kickoffs (FIFA's post-Gijón fix) **cannot** remove. Define
**manipulable match-states** (advancement-optimal action ≠ win-maximizing action), count their rate
and stakes under 32 vs 48 via the simulator, and state the general **breadth–fidelity–
strategyproofness trilemma**. Lineage: Gibbard–Satterthwaite / mechanism design (broad significance).
Single striking number: the **expansion manipulability multiplier**. Live test: pre-register the
flagged MD3 states (~2026-06-24) and observe whether implicated teams exploit them. Full formalism
in [`THEORY.md`](THEORY.md). *Lead angle: it combines a (restricted) formal result, a single
reproducible estimate, and a prospective prediction that the live tournament can falsify.*

### #1 (support, reframed). The breadth–fidelity frontier of selection systems
*Reframed away from "inclusivity/dilution" (politically loaded) to a neutral mechanism property.*
Define **selection efficiency** = P(strongest entity actually wins) and trace where 32→48 moves the
tournament on a breadth-vs-fidelity Pareto frontier. Generalizes to any selection system (grants,
hiring, elections) without DEI-coded language. Provides the "why it matters beyond football" framing
for #4.

### #2/#3 (instrument). Entropy / predictability machinery
Outcome **entropy / surprisal**, competitive-balance index, and the **entropy-collapse curve** (how
fast the champion distribution sharpens per matchday). This is the *measurement spine* used to value
manipulable states ($V_{\text{adv}}$) and to quantify how expansion redistributes suspense. Also a
clean live-trackable quantity for the pre-registration.

### (parked). "Luck of the draw" and "globalization/convergence"
Draw-luck decomposition (title attributable to bracket luck, 32 vs 48) and confederation-gap
convergence. Good supporting results or a second paper; not the lead.

**Spine:** Lead with **#4** (the theorem + the number + the live test), motivate significance with
**#1 reframed** (breadth–fidelity of selection systems generally), measure everything with the
**#2/#3** entropy instrument. The through-line: *expanding access to a competition trades selection
accuracy for breadth at a measurable cost in manipulability; the 2026 expansion is a clean test case.*

## 4. Methods sketch

- **Team strength model:** two independent families — time-varying Elo, and a hierarchical
  Bayesian Poisson goals model (independent; the Dixon–Coles low-score correction is not yet
  implemented — Tier 3 calibration TODO) — fit to historical internationals →
  calibrated match-outcome and scoreline probabilities. Both are implemented; results are
  reported under each for robustness. Emphasis on **calibration and proper scoring (Brier,
  log-loss, RPS)**, not raw accuracy. (No separate gradient-boosted/neural "ML layer" is used;
  if added later it would be a calibration benchmark against these baselines, not a core
  dependency — flagged so the methods stay consistent with what is actually run.)
- **Tournament simulator:** Monte Carlo over the full bracket; swap the 32- vs 48-team format and
  the draw to produce counterfactual distributions.
- **Metrics:** outcome entropy / surprisal; competitive-balance index; share of stakeless matches;
  draw-luck attribution; live win-probability volatility.
- **Pre-registration:** lock the model + predictions before the 2026 knockout rounds; score live.
  The prospective prediction is what reduces researcher degrees of freedom in the MD3 analysis.

## 5. Data strategy
See `data/README.md` for the source catalog and licensing notes.

## 6. Open decisions (for the user)
1. Anchor angle: A-lead triad (recommended) vs. single sharp angle?
2. Primary target journal: design-for Nature Human Behaviour/PNAS (recommended) vs. flagship-first?
3. Public **prospective time-stamp** of the live predictions via a Zenodo DOI + signed git tag
   (primary), with a dated arXiv note as secondary/optional reach, rather than OSF (low adoption in our
   field); the content hashes give integrity. (Big credibility win.)
4. Strength backbone: Elo-first (fast) vs. Bayesian Poisson-first (more defensible)?
