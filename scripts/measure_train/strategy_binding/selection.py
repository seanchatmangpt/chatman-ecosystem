from .subject import Refused

def _sum(c): return sum(g for _,g in c.producer_generations)
def _skew(c):
    gs=[g for _,g in c.producer_generations]
    return max(gs)-min(gs) if gs else 0

def select(policy, candidates):
    complete=[c for c in candidates if c.complete]
    if not complete: raise Refused("REFUSED[NO_COMPLETE_CUT]")
    if policy.strategy=="LATEST_COMPLETE":
        key=lambda c:(c.generation,_sum(c),-_skew(c),c.cut_id)
    elif policy.strategy=="MAX_FRESHNESS":
        key=lambda c:(_sum(c),c.generation,-_skew(c),c.cut_id)
    elif policy.strategy=="MIN_SKEW":
        key=lambda c:(-_skew(c),_sum(c),c.generation,c.cut_id)
    else: raise Refused("REFUSED[UNKNOWN_SELECTION_STRATEGY]")
    return max(complete,key=key)
