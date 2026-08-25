from .subject import Refused

def classify_freshness(claim, now, ttl_seconds=None):
    if now.tzinfo is None or claim.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
    age=(now-claim.observed_at).total_seconds()
    if age < 0: raise Refused("REFUSED[FUTURE_EVIDENCE]")
    if ttl_seconds is None: return "UNBOUNDED"
    if ttl_seconds < 0: raise Refused("REFUSED[INVALID_TTL]")
    return "FRESH" if age <= ttl_seconds else "STALE"
