from .subject import Refused

def admit_calibration(calibration, frontier, min_support=4, max_fp=0.10):
    if frontier.state!="CALIBRATED" or calibration.state!="CALIBRATED":
        raise Refused("REFUSED[UNCALIBRATED_RELATION]")
    if calibration.support<min_support:
        raise Refused("REFUSED[INSUFFICIENT_RELATION_SUPPORT]")
    if calibration.false_positive_rate>max_fp:
        raise Refused("REFUSED[EXCESS_FALSE_EQUIVALENCE]")
    return "ADMITTED"
