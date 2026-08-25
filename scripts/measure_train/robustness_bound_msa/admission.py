from .subject import Refused
def admit_case(subject, case, current_model, now, max_width=None):
    if case.subject != subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
    if case.observed_at > now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
    if case.bound.estimator != current_model.estimator: raise Refused("REFUSED[FOREIGN_ESTIMATOR]")
    if current_model.state != "CALIBRATED": raise Refused("REFUSED[UNCALIBRATED_BOUND_MODEL]")
    if max_width is not None and case.bound.width > max_width: raise Refused("REFUSED[UNINFORMATIVE_BOUND]")
    return "ADMITTED"
