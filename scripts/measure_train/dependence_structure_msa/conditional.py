from dataclasses import dataclass
from .contingency import contingency
from .association import association

@dataclass(frozen=True)
class ConditionalProfile:
    stratum_phi: tuple[tuple[str,float], ...]
    pooled_phi: float
    simpson_reversal: bool

def conditional_profile(rows):
    rows=tuple(rows)
    by={}
    for row in rows:
        by.setdefault(row.stratum,[]).append(row)
    strat=tuple(sorted((k,association(contingency(v)).phi) for k,v in by.items()))
    pooled=association(contingency(rows)).phi
    signs={1 if v>0 else -1 if v<0 else 0 for _,v in strat}
    nonzero={s for s in signs if s}
    pooled_sign=1 if pooled>0 else -1 if pooled<0 else 0
    reversal=bool(nonzero) and len(nonzero)==1 and pooled_sign and pooled_sign not in nonzero
    return ConditionalProfile(strat,pooled,reversal)
