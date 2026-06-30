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

## 4. Theory: a restricted theorem (proven) and the general conjecture (open)

### 4.1 What within-group simultaneity can and cannot remove

**Setup.** Final matchday. *Within-group simultaneity* (FIFA's post-Gijón rule): the two matches of
each group kick off together; **across** groups the order is arbitrary (the actual 2026 schedule
spreads the 12 groups over several days). Team $t$'s **decision information set** $I_t$ is the set of
match results completed strictly before $t$'s kickoff; within-group simultaneity guarantees $I_t$
excludes $t$'s own match *and* its group-mate match, but it includes other groups that have already
finished. Actions $\mathcal{A}=\{$WIN,DRAW,LOSE$\}$ and $V_{\text{adv}}$ are as pinned in §2.

> **Definition (simultaneity-irreducible).** A manipulable state is *simultaneity-irreducible* if
> $a^\*_{\text{adv}}(t)\neq$ WIN persists under **every** schedule respecting within-group
> simultaneity — equivalently, the deciding dependency is on matches **outside** $t$'s group, which
> within-group simultaneity never conceals.

> **Proposition 1 (no pure-qualification manipulation, either format).** Fix all results other than
> $t$'s final match. In both $M_{32}$ and $M_{48}$ the set of $t$'s own results for which $t$
> *advances* is upward-closed in the order LOSE $\prec$ DRAW $\prec$ WIN. Hence WIN maximizes
> $\Pr[t\text{ advances}]$ for any beliefs about the unknown group-mate match: no team has a
> manipulation incentive whose objective is **qualification alone**.

*Proof.* A better own result strictly increases $t$'s points and weakly improves its goal difference
and goals scored, weakly worsens its opponent's, and leaves all other teams' records unchanged. Every
ranking $t$ is entered into — its group ranking (points, GD, GF, head-to-head) and, under $M_{48}$,
the best-third ranking (points, GD, GF) — is monotone non-decreasing in $t$'s record. So advancing
under DRAW implies advancing under WIN, and LOSE $\preceq$ DRAW; the qualifying set is upward-closed.
Upward-closedness is preserved under expectation over the unknown group-mate result, so WIN maximizes
$\Pr[\text{advance}]$ pointwise and in expectation. $\qquad\blacksquare$

Consequently **all** group-stage manipulability is *path/seeding-valued*, not threshold-valued — which
is exactly why the simulated qualification-objective manipulability is $\approx 0$ in both formats
(RESULTS.md R10).

> **Proposition 2 (the best-third rule creates simultaneity-irreducible manipulable states).** Under
> $M_{48}$ there exist states — with at least one best-third-relevant group completed before $t$'s
> match — in which $t$'s advancement-optimal action is **not** WIN and the incentive is
> simultaneity-irreducible. No state of this *type* exists under $M_{32}$, where third place is
> elimination.

*Proof (construction).* Group $G=\{t,X,Y,Z\}$; MD3 pairs $t$–$Z$ and $X$–$Y$ (simultaneous). Choose
pre-MD3 points so that $X$ has clinched 1st and $Y$ is eliminated irrespective of the $X$–$Y$ result,
and the 2nd-vs-3rd place between $t$ and $Z$ is decided **solely by the $t$–$Z$ match**: $t$ finishes
2nd if it draws or wins and 3rd if it loses (e.g. $t$ leads $Z$ by one point entering MD3). Thus
$t$'s finishing position is a function of its own action alone — the concealed $X$–$Y$ match is
irrelevant. Now suppose the other groups have completed (so their results are in $I_t$) and are such
that (i) $t$'s 3rd-place record would still rank inside the best eight thirds, so $t$ **qualifies
either way**, and (ii) the official R32 table sends a 3rd-from-$G$ to a bracket slot whose path is
strictly weaker (higher $V_{\text{adv}}$) than the slot a 2nd-from-$G$ receives. Then
$V_{\text{adv}}(t,\text{LOSE}{\to}\text{3rd}) > V_{\text{adv}}(t,\text{WIN}{\to}\text{2nd})$, so
$a^\*_{\text{adv}}=$ LOSE $\neq$ WIN: the state is manipulable. The deciding quantities — that $t$
still qualifies as a third, and that the 3rd slot's path is easier — are both **cross-group**
functions (the best-third pool and the R32 fill), so the incentive is simultaneity-irreducible.
Under $M_{32}$ the identical configuration gives 3rd place value $0$ (elimination), so WIN weakly
dominates and the state is not manipulable: the channel is absent. $\qquad\blacksquare$

**Honest scope — what is *not* claimed.** Proposition 2 is an existence result for a channel *unique
to* $M_{48}$; it is **not** a claim that $M_{32}$ is manipulation-free. Path/seeding manipulation
(e.g. preferring 2nd to 1st for an easier draw) exists under $M_{32}$ too, and some of it is also
simultaneity-irreducible. What the best-third rule adds is a qualification channel (3rd place) whose
*availability* and *bracket slot* are cross-group functions, so the manipulable states it creates are
cross-group by construction. The *magnitude* of the difference is the empirical contribution:
cross-group-manipulable share is identically $0$ under $M_{32}$ and $\approx 0.48$ under $M_{48}$
(R12, N=400), and the best-third rule alone accounts for essentially the whole multiplier ($1.72$ of
the $1.66$, field/groups/draw held fixed).

**Remark (could simultaneity be lifted to fix this?).** Eliminating the Proposition-2 incentive would
require synchronizing *all* groups that feed a common best-third pool into one tournament-wide
simultaneous final matchday — the Gijón fix at tournament scale — which is generally infeasible
(venues, time zones, broadcast) and, even if imposed, only removes *informed* manipulation (replacing
it with a team unable to know whether to deviate). Within-group simultaneity, the rule FIFA actually
uses, cannot remove it.

### 4.2 The general conjecture (open)

> **Conjecture (breadth–fidelity–strategyproofness trilemma).** No group-stage advancement
> mechanism can simultaneously satisfy: (i) **breadth** — admit more than a threshold fraction of
> entrants relative to knockout slots; (ii) **bounded cost** — fixed, equal number of matches per
> entrant; and (iii) **strategyproofness** — no team ever has $\Delta(t,s)>0$. The 32→48 expansion
> is a concrete move across this frontier: it buys breadth at a measurable price in manipulability.

This remains a **conjecture**, not a theorem: the breadth threshold in (i) is undefined (§6 open
task), and (iii) as stated is too strong given Proposition 1's caveat that some seeding manipulation
exists at every breadth. §4.1 is the proven kernel — a restricted, cross-group existence result with a
measured magnitude. The trilemma is the aspirational generalization; **the paper's claims rest on
§4.1 (proven) + the empirical decomposition (R9), and the title/abstract are phrased accordingly
(“increases”, not “breaks”).** Lineage: Gibbard–Satterthwaite / Duggan–Schwartz; relate but do not
assert equivalence.

### 4.3 Equilibrium treatment of the group finale (addressing reviewer R1)

The primary analysis is **decision-theoretic**: a team's advancement-optimal action when all other
matches are sampled from the fixed strength model. But a group's two final-matchday matches are
played simultaneously and all four teams are strategic, so we also study the finale as a
simultaneous-move game and ask whether the manipulability flag — and the cross-group share, the
headline structural claim — is invariant to the solution concept.

**Game.** Players: the four teams of a group at MD3. Each chooses a target result for its own match,
$a_i\in\{$WIN,DRAW,LOSE$\}$ (§2). The two matches are **resolved** from the targets by: if the two
teams in a match desire a common result (one targets WIN and the other LOSE toward the same side, or
both target DRAW), that result is realized deterministically (a minimal scoreline) — the
collusion-feasible / mutual-interest case (the Gijón mechanism, which the coarse single-team action
space could not represent); otherwise the targets conflict and the match is a genuine contest sampled
from the strength model. Payoffs are $V_{\text{adv}}$ (expected knockout rounds won) with both group
matches pinned by the profile and all other groups sampled.

**Solution and reporting.** We compute pure-strategy Nash equilibria by best-response dynamics from
the all-WIN profile (`equilibrium.solve_group`); profiles that cycle are flagged as having no pure NE.
A state is *equilibrium-manipulable* for $t$ if $t$'s equilibrium action $\neq$ WIN. The structural
claim is robust iff the cross-group share persists under this notion; we will report the equilibrium
manipulability rate and cross-group share against the decision-theoretic baseline.

**Status (increment 2).** Solver hardened: best-response dynamics now switches a team's action only on
a **significant improvement** (`min_improve`, tied to Monte-Carlo noise), which removes the
noise-driven cycling and the spurious "everyone-draws" basin of increment 1 and keeps WIN sticky
(a team is flagged manipulable only on a clear gain). `classify` reports per-team equilibrium
manipulability + cross-group status; `run_equilibrium.py` sweeps all groups at the real pre-MD3 state.
**Preliminary finding:** the hardened solver reaches **pure Nash equilibria** in several groups (e.g.
Group J), and — the point R1 raised — **cross-group manipulability persists under the equilibrium
notion** (e.g. Group B's Bosnia is equilibrium-manipulable *and* cross-group, q3≈1), so the structural
claim is not merely a decision-theoretic artifact. Remaining (increment 3): some groups have **no pure
NE** (cycle → need mixed-strategy / fictitious-play handling), and the full equilibrium-vs-decision-
theoretic cross-group-share comparison is being computed (`results/equilibrium.json`). The headline
results stay the decision-theoretic estimate; the equilibrium analysis is reported as robustness.

## 5. Empirical test (this month — the live differentiator)

- **Publicly time-stamp** (Zenodo DOI + signed git tag, before MD3; arXiv note secondary): the explicit list of *theoretically manipulable*
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
