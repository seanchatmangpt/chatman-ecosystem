from .subject import Refused

def epoch_freshness(epoch, now, ttl_seconds):
    if ttl_seconds < 0: raise Refused("REFUSED[INVALID_TTL]")
    age=(now-epoch.observed_at).total_seconds()
    if age < 0: raise Refused("REFUSED[FUTURE_EPOCH]")
    return "FRESH" if age <= ttl_seconds else "STALE"
