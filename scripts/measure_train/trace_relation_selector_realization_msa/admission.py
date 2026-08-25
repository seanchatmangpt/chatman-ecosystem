from .subject import Refused

def admit_decision(decision, frontier, now, max_age_seconds, max_predicted_error_ppm=250000):
    if decision.decided_at > now:
        raise Refused("REFUSED[FUTURE_DECISION]")
    age=(now-decision.decided_at).total_seconds()
    if age > max_age_seconds:
        raise Refused("REFUSED[STALE_SELECTOR_DECISION]")
    matches=[f for f in frontier if f.selector==decision.selector]
    if len(matches)!=1:
        raise Refused("REFUSED[SELECTOR_FRONTIER_MISMATCH]")
    if matches[0].state!="CALIBRATED":
        raise Refused("REFUSED[UNCALIBRATED_SELECTOR]")
    if decision.predicted_error_ppm>max_predicted_error_ppm:
        raise Refused("REFUSED[EXCESSIVE_PREDICTED_ERROR]")
    return "ADMITTED"
