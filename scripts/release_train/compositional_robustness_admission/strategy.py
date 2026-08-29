from enum import Enum
from .portfolio import Portfolio
from .refusal import Refused

class Strategy(str, Enum):
    HOLD="HOLD"; MAX_LOWER="MAX_LOWER"; MIN_WIDTH="MIN_WIDTH"; MAX_BREAKDOWN="MAX_BREAKDOWN"; MIN_COST="MIN_COST"; MINIMAX_LATENCY="MINIMAX_LATENCY"

def select(items: tuple[Portfolio,...], strategy: Strategy, current: tuple[str,...]=()) -> Portfolio:
    if not items: raise Refused("NO_PORTFOLIO_CANDIDATES")
    if strategy is Strategy.HOLD:
        for p in items:
            if p.digests == tuple(sorted(current)): return p
        raise Refused("HOLD_NOT_AVAILABLE")
    keys={
        Strategy.MAX_LOWER: lambda p:(p.interval.lower, tuple(reversed(p.digests))),
        Strategy.MIN_WIDTH: lambda p:(-p.interval.width, tuple(reversed(p.digests))),
        Strategy.MAX_BREAKDOWN: lambda p:(p.breakdown_gamma, tuple(reversed(p.digests))),
        Strategy.MIN_COST: lambda p:(-p.cost, tuple(reversed(p.digests))),
        Strategy.MINIMAX_LATENCY: lambda p:(-p.latency, tuple(reversed(p.digests))),
    }
    return max(items, key=keys[strategy])
