from datetime import datetime, timedelta
from .subject import Refusal
from .witness import Witness

def require_fresh(witnesses: list[Witness], now: datetime, max_age: dict[str,timedelta]):
    if now.tzinfo is None: raise Refusal("NAIVE_NOW")
    fresh=[]
    for w in witnesses:
        if w.observed_at > now: raise Refusal("FUTURE_EVIDENCE")
        ttl=max_age.get(w.axis.value)
        if ttl is not None and now-w.observed_at > ttl: continue
        fresh.append(w)
    return tuple(fresh)
