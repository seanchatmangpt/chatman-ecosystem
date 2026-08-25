from enum import StrEnum
from .errors import Refused
class RobustStrategy(StrEnum): MAX_LOWER='MAX_LOWER'; MIN_WIDTH='MIN_WIDTH'; MAX_BREAKDOWN='MAX_BREAKDOWN'; HOLD='HOLD'
def select(candidates,strategy):
    c=tuple(candidates)
    if not c: raise Refused('REFUSED_NO_CANDIDATES')
    if strategy is RobustStrategy.MAX_LOWER: return max(c,key=lambda x:(x.interval.lower,-x.interval.width,x.policy_digest))
    if strategy is RobustStrategy.MIN_WIDTH: return min(c,key=lambda x:(x.interval.width,-x.interval.lower,x.policy_digest))
    if strategy is RobustStrategy.MAX_BREAKDOWN: return max(c,key=lambda x:(x.breakdown or 0,x.interval.lower,x.policy_digest))
    return c[0]
