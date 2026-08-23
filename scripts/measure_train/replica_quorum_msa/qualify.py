from .window import admit_window
from .quorum import classify_quorum
from .observability import observability
from .temporal import temporal_violations
from .frontier import current_frontier,admit_current
from .standing import bounded_standing
from .receipt import manufacture_receipt
from .telemetry import project
def qualify(subject,universe,observations,window,models,dependency_standings=(),parent_receipt=None):
    admitted=admit_window(observations,window)
    quorum=classify_quorum(universe,admitted)
    obs=observability(universe,admitted)
    violations=temporal_violations(admitted)
    frontier=current_frontier(models)
    calibration_state="INSUFFICIENT" if frontier is None else frontier.state
    if frontier is not None and frontier.state=="CALIBRATED": admit_current(frontier,frontier)
    standing=bounded_standing(quorum,calibration_state,violations,dependency_standings)
    receipt=manufacture_receipt(subject,quorum,obs,frontier,standing,parent_receipt)
    return {"quorum":quorum,"observability":obs,"violations":violations,"standing":standing,
            "receipt":receipt,"telemetry":project(subject,admitted,quorum,standing),"actuation_performed":False}
