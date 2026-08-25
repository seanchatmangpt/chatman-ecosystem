from datetime import datetime

def classify_freshness(observed_at:datetime, now:datetime, ttl_seconds:int|None):
    if ttl_seconds is None: return "UNBOUNDED"
    if ttl_seconds < 0: raise ValueError("REFUSED[NEGATIVE_TTL]")
    if observed_at.tzinfo is None or now.tzinfo is None: raise ValueError("REFUSED[NAIVE_FRESHNESS_CLOCK]")
    age=(now-observed_at).total_seconds()
    if age < 0: return "REFUSED[FUTURE_EVIDENCE]"
    return "FRESH" if age <= ttl_seconds else "STALE"
