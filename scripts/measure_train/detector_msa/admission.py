from .subject import Refused

def admit_current_detector(subject, policy, calibration, frontier, observed_subject, observed_at, now):
    if observed_subject != subject:
        raise Refused("REFUSED[FOREIGN_DETECTOR_SUBJECT]")
    if observed_at.tzinfo is None or now.tzinfo is None:
        raise Refused("REFUSED[NAIVE_ADMISSION_TIME]")
    if observed_at > now:
        raise Refused("REFUSED[FUTURE_DETECTOR_EVIDENCE]")
    current = {p.detector_id: (p, c) for p, c in frontier}.get(policy.detector_id)
    if current is None or current[0].fingerprint != policy.fingerprint:
        raise Refused("REFUSED[STALE_DETECTOR_POLICY]")
    if current[1] != calibration:
        raise Refused("REFUSED[STALE_DETECTOR_CALIBRATION]")
    if calibration.state != "CALIBRATED":
        raise Refused(f"REFUSED[DETECTOR_{calibration.state}]")
    return "ADMITTED"
