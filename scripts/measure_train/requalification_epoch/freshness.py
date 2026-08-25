from .subject import Refused

def classify_freshness(item, now, ttl_seconds=None):
    if now.tzinfo is None or now.utcoffset() is None: raise Refused("REFUSED[NAIVE_NOW]")
    age=(now-item.observed_at).total_seconds()
    if age < 0: raise Refused("REFUSED[FUTURE_EVIDENCE]")
    if ttl_seconds is None: return "UNBOUNDED"
    if ttl_seconds < 0: raise Refused("REFUSED[INVALID_TTL]")
    return "FRESH" if age <= ttl_seconds else "STALE"
