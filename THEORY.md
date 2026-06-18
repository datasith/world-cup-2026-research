# Theory: manipulability of the 48-team World Cup format

Formal backbone for the lead result. Goal: make every claim falsifiable and computable from the
simulator, and state the general (sport-independent) result the flagship framing rests on.

---

## 1. Setup

A tournament **format** is a mechanism $M$ mapping a profile of match results to a final ranking
(in particular, a champion and a set of advancing teams). The **group stage** of $M$ partitions
teams into groups; an **advancement rule** $A$ selects which teams progress to the knockout bracket
and *where they are seeded*.

- **32-team format** $M_{32}$: 8 groups of 4; top 2 per group advance (16 teams). Advancement of
  team $t$ depends only on results *within* $t$'s group.
- **48-team format** $M_{48}$: 12 groups of 4; top 2 per group (24) **plus the 8 best
  third-placed teams** advance to a Round of 32. Advancement of a third-placed team depends on a
  **cross-group comparison** of third-place records.

We attach to each team a **strength model** (Elo / Bayesian-Poisson) that yields, for any match,
a distribution over results. This converts $M$ into a stochastic process we can simulate.

## 2. Manipulable match-states

Consider the decision point of a team $t$ entering a match $m$ in a given tournament state $s$
(scores so far, other groups' standings).

**Action space (pinned).** The action set is the coarse target-result space
$\mathcal{A}=\{\text{WIN},\text{DRAW},\text{LOSE}\}$. An action is realized by sampling the match
scoreline from the strength model *conditioned* on that result (engine `_sample_conditioned`); it
is a target over result distributions, not an exact score. $a^\*_{\text{win}}(t,s)\equiv\text{WIN}$
by construction (targeting a win maximizes $\Pr[t\text{ wins }m]$). *Limitation:* this coarse space
does not represent within-WIN **scoreline targeting** (the Gijón collusion pattern needs a finer
action space); see §6.

**Opponent model (pinned).** $V_{\text{adv}}$ is a **decision-theoretic best response**: all other
matches (including the simultaneous same-group match and other groups) are sampled from the *fixed*
strength model, not played strategically. So a "manipulable state" is a property of $t$'s argmax
against fixed opponents, **not** a Nash equilibrium of the group-finale game (see §6 / open tasks).

**Advancement value $V_{\text{adv}}$ (pinned — single definition).** Conditioning $m$ on action
$a$, Monte-Carlo-simulate the remainder of the tournament; then
$$V_{\text{adv}}(t,s,a) \;=\; \mathbb{E}\big[\text{knockout rounds $t$ wins}\big],$$
counting $0$ if $t$ fails to advance. This single functional **subsumes** "probability of advancing"
(a non-qualifier scores $0$) **and** "advancing into a weaker bracket path" (an easier draw yields
more expected rounds), so it is the canonical $V_{\text{adv}}$ used for all reported $\rho$, $\Delta$
and multiplier numbers. Two alternative functionals — $V^{\text{qual}}=\Pr[t\text{ advances}]$ and
$V^{\text{champ}}=\Pr[t\text{ wins the title}]$ — are reported as a **robustness range** in
RESULTS.md R10 (the conclusions are reported against, not assumed invariant to, the choice).

> **Definition (manipulable state).** State $s$ is **manipulable for team $t$** if
> $a^\*_{\text{adv}}(t,s) \neq a^\*_{\text{win}}(t,s)$ — i.e. $t$'s advancement-optimal action is
> *not* to maximize its chance of winning the match. The **magnitude** of manipulability is
> $\Delta(t,s) = V_{\text{adv}}\big(a^\*_{\text{adv}}\big) - V_{\text{adv}}\big(a^\*_{\text{win}}\big) \ge 0$,
> the progression value a team forgoes by "honestly" trying to win. ($\Delta$ is in the units of the
> chosen $V_{\text{adv}}$: expected knockout rounds for the canonical definition.)

Special cases of interest:
- **Tanking:** $a^\*_{\text{adv}}$ is to lose or draw (e.g. to avoid a strong knockout opponent or
  reach a softer bracket quadrant).
- **Scoreline targeting:** both teams in $m$ share an interval of scorelines that advances both at
  a third team's expense — the **Gijón** pattern (collusion-feasible).
- **Cross-group dead/contingent rubbers:** under $M_{48}$, a third-placed team's required result
  depends on *other groups still in progress*, so within-group **simultaneity does not remove**
  $\Delta(t,s)>0$. This is the structural novelty.

## 3. Quantities to report (computable from the simulator)

For a format $M$, over Monte-Carlo tournaments:

1. **Manipulability rate** $\rho(M) = \Pr[s \text{ is manipulable for some } t]$ across decision
   states (esp. final-matchday states).
2. **Expected manipulability mass** $\bar\Delta(M) = \mathbb{E}[\Delta(t,s)\,]$ — average stakes of
   manipulation opportunities.
3. **Simultaneity-irreducible share**: fraction of manipulable states whose dependency is
   *cross-group* (hence not fixable by simultaneous kickoffs). Target headline: this share is
   $>0$ for $M_{48}$ and (near) $0$ for $M_{32}$.
4. **Expansion multiplier**: $\rho(M_{48})/\rho(M_{32})$ and $\bar\Delta(M_{48})/\bar\Delta(M_{32})$
   — the single striking numbers.

## 4. The general claim (what makes it flagship-shaped)

> **Conjecture (breadth–fidelity–strategyproofness trilemma).** No group-stage advancement
> mechanism can simultaneously satisfy: (i) **breadth** — admit more than a threshold fraction of
> entrants relative to knockout slots; (ii) **bounded cost** — fixed, equal number of matches per
> entrant; and (iii) **strategyproofness** — no team ever has $\Delta(t,s)>0$. The 32→48 expansion
> is a concrete move across this frontier: it buys breadth at a measurable price in manipulability.

This is the impossibility-frontier statement (Gibbard–Satterthwaite / mechanism-design lineage).
We don't need to *prove* the full impossibility to publish; we need to (a) define the frontier
precisely, (b) show $M_{48}$ sits strictly worse than $M_{32}$ on it, and (c) argue the trade-off
is structural, not incidental. A formal proof of a restricted version would be a major bonus.

## 5. Empirical test (this month — the live differentiator)

- **Pre-register** (OSF, before MD3, ~2026-06-24): the explicit list of *theoretically manipulable*
  group-finale states the simulator flags, and the result each implicated team would "want."
- **Observe** MD3: did implicated teams play toward the manipulation-optimal result? Use live
  win-probability volatility / shot-rate / pressing intensity as passivity proxies.
- **Score**: predicted-vs-observed. A pre-registered, then realized, manipulation event is the
  headline. *Caveat:* passivity is confoundable (fatigue, rotation, tactics), so the **theoretical
  manipulable-state count is the rigorous core**; live detection is corroborating evidence, framed
  as such.

## 6. Open theory tasks
- [x] **Operationalize $V_{\text{adv}}$** — pinned in §2 as expected knockout rounds won (canonical),
  with $V^{\text{qual}}$ and $V^{\text{champ}}$ as a reported robustness range (RESULTS.md R10).
- [x] **Define the action space** — pinned in §2 as $\{$WIN,DRAW,LOSE$\}$ target results mapped to
  conditioned scoreline distributions, with the decision-theoretic opponent model stated.
- [ ] **Finer action space for scoreline targeting** (within-WIN Gijón collusion) — the coarse W/D/L
  set cannot represent it; needed to capture the collusion-feasible special case fully.
- [ ] **Equilibrium treatment** — promote the decision-theoretic best response to a (Bayes-)Nash
  equilibrium of the simultaneous group-finale game, or state explicitly that results are
  best-response manipulability (currently the latter).
- [ ] Pin the breadth threshold in the trilemma; relate to (#groups, group size, #wildcards).
- [ ] Decide whether to attempt a restricted formal impossibility proof.
