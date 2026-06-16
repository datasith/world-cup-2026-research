# World Cup 2026 — Research Design Plan

**Working title (placeholder):** *A natural experiment in tournament design: how expanding the
World Cup to 48 teams reshapes competitive balance, predictability, and upset dynamics.*

Status: scaffolding / idea selection. Last updated 2026-06-16.

---

## 1. The honest publishing landscape (literature scan, 2026-06-16)

Before picking an angle, here is what the literature actually shows. This matters because Nature
and Science (the *flagship* journals) reject ~92% of submissions and almost never publish a sports
analysis unless it answers a question of broad scientific significance.

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
  (~9 Mt), "most polluting ever." Mostly industry reports and press, not peer-reviewed science.
  The user's instinct is right — this is crowded and not a flagship path.

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

### A. "The expansion paradox" — does adding weaker teams make the tournament *more* or *less* predictable? ⭐ lead
Reframe the format change as a perturbation. Quantify, with one clean information-theoretic metric
(e.g. tournament-outcome **entropy** / surprisal, and a "competitive balance" index), whether the
48-team format increases the share of stakeless/foregone-conclusion matches (Csató's worry) **or**
increases net upset surprise. Pre-register the prediction *before* the knockout stage and score it
against the live 2026 results. Generalizable claim: structure, not field strength, sets the
predictability of competitive systems.

### B. "Manufactured drama" — measuring the entertainment/competitiveness trade-off of the third-place qualifier
The 48-team format advances 8 best third-placed teams, creating dead-rubber and collusion-risk
games (cf. Disgrace of Gijón). Build a within-tournament causal contrast of match "competitiveness"
(live win-probability volatility) in matches with vs. without qualification stakes. Novelty: a
real-time **stakes** instrument.

### C. "Path dependence & the luck of the draw" — how much does the bracket, not the team, decide the champion?
Counterfactual re-draw simulation: hold team strengths fixed, resample the draw 10^5×, measure how
much a title is attributable to draw luck under 32 vs 48 formats. Flagship hook: quantifying
merit-vs-luck in a high-stakes selection system.

### D. "Globalization of the game" — does expansion narrow or widen the strength gap between
confederations? Test whether more slots accelerate competitive convergence (a development-economics
flavored question). Pairs naturally with B/C.

**Suggested spine:** Lead with **A** (the testable, pre-registered headline), support with **C**
(the luck decomposition) and **B** (the within-tournament causal stakes contrast). That triad is a
coherent, flagship-shaped story: *structure controls predictability, luck, and stakes.*

## 4. Methods sketch

- **Team strength model:** time-varying Elo (or a Bayesian Poisson/bivariate-Poisson goals model,
  e.g. Dixon-Coles) fit to historical internationals → calibrated match-outcome probabilities.
- **ML layer:** gradient-boosted / neural models on match + (where available) event-level features
  for outcome and goal-difference prediction; used for *calibrated probabilities*, benchmarked vs.
  the Elo/Poisson baseline. Emphasis on **calibration and proper scoring (Brier, log-loss, RPS)**,
  not raw accuracy — reviewers in this space punish accuracy-only claims.
- **Tournament simulator:** Monte Carlo over the full bracket; swap the 32- vs 48-team format and
  the draw to produce counterfactual distributions.
- **Metrics:** outcome entropy / surprisal; competitive-balance index; share of stakeless matches;
  draw-luck attribution; live win-probability volatility.
- **Pre-registration:** lock the model + predictions before the 2026 knockout rounds; score live.
  This is the credibility centerpiece.

## 5. Data strategy
See `data/README.md` for the source catalog and licensing notes.

## 6. Open decisions (for the user)
1. Anchor angle: A-lead triad (recommended) vs. single sharp angle?
2. Primary target journal: design-for Nature Human Behaviour/PNAS (recommended) vs. flagship-first?
3. Do we commit to a public **pre-registration** (OSF) of the live predictions? (Big credibility win.)
4. Strength backbone: Elo-first (fast) vs. Bayesian Poisson-first (more defensible)?
