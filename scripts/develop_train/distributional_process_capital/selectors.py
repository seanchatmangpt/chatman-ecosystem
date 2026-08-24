from enum import Enum
class Strategy(str,Enum):
    MIN_NOMINAL="MIN_NOMINAL"
    MIN_WORST="MIN_WORST"
    MIN_RADIUS="MIN_RADIUS"
    MAX_SUPPORT="MAX_SUPPORT"
    MINIMAX_REGRET="MINIMAX_REGRET"

def select(candidates,strategy):
    cs=tuple(candidates)
    if strategy==Strategy.MIN_NOMINAL:
        return min(cs,key=lambda c:(c.nominal,c.name))
    if strategy==Strategy.MIN_WORST:
        return min(cs,key=lambda c:(c.worst,c.name))
    if strategy==Strategy.MIN_RADIUS:
        return min(cs,key=lambda c:(c.radius,c.name))
    if strategy==Strategy.MAX_SUPPORT:
        return max(cs,key=lambda c:(c.support,-c.worst,c.name))
    best=min(c.worst for c in cs)
    return min(cs,key=lambda c:(c.worst-best,c.nominal,c.name))
