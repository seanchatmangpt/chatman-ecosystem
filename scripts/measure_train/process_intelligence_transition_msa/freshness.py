from .subject import Refused

def freshness(evidence, now, ttl_seconds):
    if ttl_seconds < 0:
        raise Refused("REFUSED[INVALID_TTL]")
    age = (now - evidence.observed_at).total_seconds()
    if age < 0:
        raise Refused("REFUSED[FUTURE_EVIDENCE]")
    return "FRESH" if age <= ttl_seconds else "STALE"
