from .admission import admit
from .support import profile,require_support
from .calibration import calibrate
from .methodology import coverage
from .failure_worlds import REQUIRED
from .standing import standing
from .receipt import manufacture
def qualify(subject,observations,now,dependency_states=(),correspondence=False,failure_worlds=()):
    rows=admit(subject,observations,now)
    support=profile(rows)
    require_support(support)
    n,mae,cal_state=calibrate(rows)
    methods=coverage(rows)
    failures=set(failure_worlds)>=REQUIRED
    status=standing(calibration_state=cal_state,drifted=False,dependency_states=dependency_states,
                    methodology_complete=methods["complete"],correspondence=correspondence,failure_complete=failures)
    census={"observations":len(rows),"labeled":support.labeled,"ess":[support.ess.numerator,support.ess.denominator],
            "calibration":cal_state,"mae":[mae.numerator,mae.denominator],"methodology_complete":methods["complete"],
            "correspondence":correspondence,"failure_complete":failures}
    receipt=manufacture(subject,status,census)
    telemetry=({"activity":"outcome_capital_transport_qualification","repo":subject.repo,"sha":subject.sha,
                "standing":status,"observations":len(rows)},)
    return {"standing":status,"census":census,"receipt":receipt,"telemetry":telemetry,"actuation_performed":False}
