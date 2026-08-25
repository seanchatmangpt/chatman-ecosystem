from fractions import Fraction
from .errors import Refused

def overlap_ratio(a,b):
    a,b=set(a),set(b)
    if not a and not b: return Fraction(0)
    return Fraction(len(a&b),len(a|b))
def higher_order_overlap(groups):
    gs=[set(g) for g in groups]
    if len(gs)<3: raise Refused('HIGHER_ORDER_SUPPORT_REQUIRED')
    union=set().union(*gs); inter=set.intersection(*gs) if gs else set()
    return Fraction(len(inter),len(union) or 1)
def require_dependence_bounds(pair_overlap,higher_overlap,max_pair,max_higher):
    if pair_overlap > Fraction(max_pair): raise Refused('PAIRWISE_DEPENDENCE_EXCESS')
    if higher_overlap > Fraction(max_higher): raise Refused('HIGHER_ORDER_DEPENDENCE_EXCESS')
    return True
