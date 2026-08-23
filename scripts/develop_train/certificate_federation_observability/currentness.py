from dataclasses import dataclass
from datetime import datetime, timezone
from .freshness import Freshness
from .observation import Relation
from .transport import TransportState
from .errors import Refused
@dataclass(frozen=True)
class Currentness: current:int; stale:int; censored:int
def evaluate(observations,max_age_seconds=900,now=None):
    now=now or datetime.now(timezone.utc); f=Freshness(max_age_seconds); current=stale=censored=0
    for o in observations:
        if o.state!=TransportState.RESOLVED or o.relation==Relation.CENSORED: censored+=1
        elif f.current(o.observed_at,now): current+=1
        else: stale+=1
    return Currentness(current,stale,censored)
def require_current(c,min_current=2):
    if c.current<min_current: raise Refused("INSUFFICIENT_CURRENT_EVIDENCE")
    return c
