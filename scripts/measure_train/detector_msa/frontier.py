from .subject import Refused

def current_calibration_frontier(policies, calibrations):
    by_detector = {}
    calibration_by_fingerprint = {item.policy_fingerprint: item for item in calibrations}
    for policy in policies:
        calibration = calibration_by_fingerprint.get(policy.fingerprint)
        if calibration is None:
            raise Refused("REFUSED[MISSING_DETECTOR_CALIBRATION]")
        previous = by_detector.get(policy.detector_id)
        if previous is None or policy.generation > previous[0].generation:
            by_detector[policy.detector_id] = (policy, calibration)
        elif policy.generation == previous[0].generation and policy.fingerprint != previous[0].fingerprint:
            raise Refused("REFUSED[DIVERGENT_DETECTOR_FRONTIER]")
    return tuple(sorted(by_detector.values(), key=lambda pair: pair[0].detector_id))
