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
(scores so far, other groups' standings). Let $a^\*_{\text{win}}(t,s)$ be the action (target
result) that maximizes $t$'s probability of *winning match $m$*, and let $a^\*_{\text{adv}}(t,s)$ be
the action that maximizes $t$'s *expected tournament progression* (probability-weighted value of
advancing, and of advancing into a weaker bracket path).

> **Definition (manipulable state).** State $s$ is **manipulable for team $t$** if
> $a^\*_{\text{adv}}(t,s) \neq a^\*_{\text{win}}(t,s)$ — i.e. $t$'s advancement-optimal action is
> *not* to maximize its chance of winning the match. The **magnitude** of manipulability is
> $\Delta(t,s) = V_{\text{adv}}\big(a^\*_{\text{adv}}\big) - V_{\text{adv}}\big(a^\*_{\text{win}}\big) \ge 0$,
> the progression value a team forgoes by "honestly" trying to win.

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
- [ ] Operationalize $V_{\text{adv}}$ (progression value incl. bracket-path strength).
- [ ] Define the action space realistically (teams target *result distributions*, not exact scores).
- [ ] Pin the breadth threshold in the trilemma; relate to (#groups, group size, #wildcards).
- [ ] Decide whether to attempt a restricted formal impossibility proof.
