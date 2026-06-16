"""World Cup 2026 analysis library.

Modules:
    elo            - time-varying Elo strength model + match-outcome probabilities
    metrics        - outcome entropy / surprisal, competitive-balance, scoring rules
    simulator      - Monte Carlo tournament simulator (32- vs 48-team formats)
    manipulability - manipulable match-states, strategyproofness stats (LEAD result)
"""

__all__ = ["elo", "metrics", "simulator", "manipulability"]
