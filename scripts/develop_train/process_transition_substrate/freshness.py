from datetime import timedelta
from .errors import Refused
def require_fresh(observed_at, now, ttl_seconds:int):
    if observed_at.tzinfo is None or now.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
    if observed_at > now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
    if now-observed_at > timedelta(seconds=ttl_seconds): raise Refused("REFUSED[STALE_EVIDENCE]")
    return True
