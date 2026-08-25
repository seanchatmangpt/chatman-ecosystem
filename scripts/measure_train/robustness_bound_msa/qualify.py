from .frontier import current_frontier
from .standing import standing
from .receipt import manufacture
def qualify(subject, calibrations, models, dependency_states=()):
    frontier=current_frontier(models)
    status=standing(calibrations,dependency_states)
    receipt=manufacture(subject,frontier,status)
    telemetry=tuple({"activity":"measure_robustness_bound","repo":subject.repo,"sha":subject.sha,
                     "estimator":m.estimator,"generation":m.generation,"state":m.state} for m in frontier)
    return {"standing":status,"frontier":frontier,"receipt":receipt,"telemetry":telemetry,"actuation_performed":False}
