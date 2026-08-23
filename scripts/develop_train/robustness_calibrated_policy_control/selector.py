from enum import Enum
from .pareto import Candidate
from .refusal import Refused
class Strategy(str,Enum):
    MAX_LOWER='MAX_LOWER'; MIN_WIDTH='MIN_WIDTH'; MAX_BREAKDOWN='MAX_BREAKDOWN'; MIN_COST='MIN_COST'; MINIMAX_LATENCY='MINIMAX_LATENCY'; HOLD='HOLD'
def select(candidates:tuple[Candidate,...], strategy:Strategy)->Candidate|None:
    if strategy is Strategy.HOLD: return None
    if not candidates: raise Refused('NO_CANDIDATES')
    keys={
      Strategy.MAX_LOWER:lambda c:(c.lower,-c.width,c.key), Strategy.MIN_WIDTH:lambda c:(-c.width,c.lower,c.key),
      Strategy.MAX_BREAKDOWN:lambda c:(c.breakdown,c.lower,c.key), Strategy.MIN_COST:lambda c:(-c.cost,c.lower,c.key),
      Strategy.MINIMAX_LATENCY:lambda c:(-c.latency,c.lower,c.key)}
    return max(candidates,key=keys[strategy])
