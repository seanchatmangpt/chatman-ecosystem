from .refusal import Refused

def admit_current(subject,policy,steps,current_policy,now,calibration,drift):
    if now.tzinfo is None or now.utcoffset() is None:
        raise Refused("REFUSED[NAIVE_NOW]")
    if policy != current_policy:
        raise Refused("REFUSED[STALE_POLICY]")
    for s in steps:
        if s.subject != subject:
            raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if s.observed_at > now:
            raise Refused("REFUSED[FUTURE_EVIDENCE]")
    if calibration["state"] == "INSUFFICIENT":
        raise Refused("REFUSED[INSUFFICIENT_POLICY_CALIBRATION]")
    if calibration["state"] == "UNRELIABLE":
        raise Refused("REFUSED[UNRELIABLE_POLICY_CALIBRATION]")
    if drift["drift"]:
        raise Refused("REFUSED[POLICY_REALIZATION_DRIFT]")
    return "ADMITTED"
