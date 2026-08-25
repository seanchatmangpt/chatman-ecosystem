from .refusal import Refused

def freshness(observation, now, ttl_seconds):
    if ttl_seconds < 0:
        raise Refused("REFUSED[INVALID_TTL]")
    age=(now-observation.observed_at).total_seconds()
    if age < 0:
        raise Refused("REFUSED[FUTURE_OBSERVATION]")
    if observation.status!="RESOLVED":
        return "CENSORED"
    return "FRESH" if age <= ttl_seconds else "STALE"
