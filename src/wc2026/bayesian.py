"""Hierarchical Bayesian Poisson goals model (Dixon-Coles style).

Each team t has latent attack a_t and defence d_t (hierarchically pooled, so
data-poor teams shrink to the mean). Goals are Poisson:

    log E[home goals] = mu + home_adv + a_home - d_away
    log E[away goals] = mu          + a_away - d_home   (neutral: home_adv=0)

Why this alongside Elo: it yields a POSTERIOR over each match-outcome
probability, so the manipulable-state flag can be reported as robust across the
posterior rather than at a point estimate (see THEORY.md sec. 5). Identical
(home, draw, away) interface to EloModel via ``outcome_probs`` on the posterior
mean, plus ``outcome_prob_samples`` for the full posterior.

Fitting ~thousands of matches with PyMC is the heaviest compute step; keep the
training window tight (recent internationals) and raise draws/chains only when
warranted. This is the first place an AWS CPU box would pay off.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class PoissonFit:
    teams: list[str]
    attack: np.ndarray          # posterior-mean attack per team
    defence: np.ndarray         # posterior-mean defence per team
    mu: float                   # baseline log-rate
    home_adv: float
    idata: object = None        # arviz InferenceData (full posterior), optional
    max_goals: int = 10         # truncation for the scoreline grid

    def _index(self, team: str) -> int | None:
        try:
            return self.teams.index(team)
        except ValueError:
            return None

    def _rates(self, home: str, away: str, neutral: bool) -> tuple[float, float]:
        hi, ai = self._index(home), self._index(away)
        a_h = self.attack[hi] if hi is not None else 0.0
        d_h = self.defence[hi] if hi is not None else 0.0
        a_a = self.attack[ai] if ai is not None else 0.0
        d_a = self.defence[ai] if ai is not None else 0.0
        ha = 0.0 if neutral else self.home_adv
        lam_h = np.exp(self.mu + ha + a_h - d_a)
        lam_a = np.exp(self.mu + a_a - d_h)
        return float(lam_h), float(lam_a)

    def strength(self, team: str) -> float:
        """Scalar overall strength = attack + defence (higher = better both ends).

        Used to rank teams for bracket seeding, mirroring EloModel.rating so the
        simulator can be driven by either strength model interchangeably.
        """
        i = self._index(team)
        if i is None:
            return 0.0
        return float(self.attack[i] + self.defence[i])

    def score_matrix(self, home: str, away: str, neutral: bool = True) -> np.ndarray:
        """P(home_goals=i, away_goals=j) on a truncated independent-Poisson grid."""
        from scipy.stats import poisson
        lam_h, lam_a = self._rates(home, away, neutral)
        g = np.arange(self.max_goals + 1)
        ph = poisson.pmf(g, lam_h)
        pa = poisson.pmf(g, lam_a)
        m = np.outer(ph, pa)
        return m / m.sum()

    def outcome_probs(self, home: str, away: str, neutral: bool = True) -> tuple[float, float, float]:
        """(P_home, P_draw, P_away) at the posterior mean -- EloModel-compatible."""
        m = self.score_matrix(home, away, neutral)
        p_home = float(np.tril(m, -1).sum())   # home_goals > away_goals
        p_draw = float(np.trace(m))
        p_away = float(np.triu(m, 1).sum())
        return p_home, p_draw, p_away


def fit(results: pd.DataFrame, draws: int = 1000, tune: int = 1500,
        chains: int = 4, target_accept: float = 0.95, seed: int = 0) -> PoissonFit:
    """Fit the hierarchical Poisson model on ``results`` with PyMC (NUTS).

    ``results`` needs columns home_team, away_team, home_score, away_score,
    neutral. Returns a PoissonFit carrying posterior-mean parameters and the
    full InferenceData for posterior-robust manipulability checks.

    Uses a **non-centered** parameterization for the team effects
    (attack/defence sampled as standardized ``*_raw`` then scaled by their group
    sd). The centered form induces a Neal funnel between each team effect and its
    hierarchical sd, which NUTS samples poorly (rhat>1.01, low ESS); non-centering
    removes it. Defaults (4 chains, tune=1500, target_accept=0.95) are sized for
    publication-grade convergence; the freeze re-fit can raise them further.
    """
    import pymc as pm

    teams = sorted(set(results.home_team) | set(results.away_team))
    tidx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    hi = results.home_team.map(tidx).to_numpy()
    ai = results.away_team.map(tidx).to_numpy()
    hg = results.home_score.to_numpy()
    ag = results.away_score.to_numpy()
    is_home = (~results.neutral.to_numpy()).astype(float)

    with pm.Model() as model:
        mu = pm.Normal("mu", 0.0, 1.0)
        home_adv = pm.Normal("home_adv", 0.2, 0.5)
        sd_att = pm.HalfNormal("sd_att", 1.0)
        sd_def = pm.HalfNormal("sd_def", 1.0)
        # non-centered team effects: standardized raw * group sd avoids the funnel
        attack_raw = pm.Normal("attack_raw", 0.0, 1.0, shape=n)
        defence_raw = pm.Normal("defence_raw", 0.0, 1.0, shape=n)
        # sum-to-zero centering keeps attack/defence identifiable against mu
        attack = pm.Deterministic("attack", attack_raw * sd_att - pm.math.mean(attack_raw * sd_att))
        defence = pm.Deterministic("defence", defence_raw * sd_def - pm.math.mean(defence_raw * sd_def))

        log_lh = mu + home_adv * is_home + attack[hi] - defence[ai]
        log_la = mu + attack[ai] - defence[hi]
        pm.Poisson("home_goals", pm.math.exp(log_lh), observed=hg)
        pm.Poisson("away_goals", pm.math.exp(log_la), observed=ag)

        idata = pm.sample(draws=draws, tune=tune, chains=chains,
                          target_accept=target_accept, random_seed=seed,
                          progressbar=False)

    post = idata.posterior
    attack_mean = post["attack"].mean(("chain", "draw")).values
    defence_mean = post["defence"].mean(("chain", "draw")).values
    return PoissonFit(
        teams=teams,
        attack=attack_mean,
        defence=defence_mean,
        mu=float(post["mu"].mean()),
        home_adv=float(post["home_adv"].mean()),
        idata=idata,
    )
