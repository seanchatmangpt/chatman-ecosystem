from .subject import Refused

def admit_current_model(candidate, frontier, drift_state, now):
    current=frontier.get("current")
    if current is None: raise Refused("REFUSED[NO_CURRENT_CALIBRATION_MODEL]")
    if candidate.model_id != current.model.model_id: raise Refused("REFUSED[STALE_CALIBRATION_MODEL]")
    if candidate.window.end > now: raise Refused("REFUSED[FUTURE_CALIBRATION_MODEL]")
    if drift_state == "DRIFT": raise Refused("REFUSED[CALIBRATION_DRIFTED]")
    if drift_state == "INSUFFICIENT": raise Refused("REFUSED[INSUFFICIENT_DRIFT_EVIDENCE]")
    if drift_state != "STABLE": raise Refused("REFUSED[UNKNOWN_DRIFT_STATE]")
    return "ADMITTED"
