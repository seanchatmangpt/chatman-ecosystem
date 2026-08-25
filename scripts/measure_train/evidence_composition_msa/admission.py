from .subject import Refused
def admit_case(subject, case, calibration, max_width=None):
    if case.subject != subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
    if calibration.state != "CALIBRATED": raise Refused("REFUSED[UNCALIBRATED_COMPOSITION]")
    if max_width is not None and case.predicted.width > max_width:
        raise Refused("REFUSED[UNINFORMATIVE_COMPOSITION_BOUND]")
    return "ADMITTED"
