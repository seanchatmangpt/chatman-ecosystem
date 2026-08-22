from .admission import admit_realization
from .realization import realize
from .proper_score import brier_score
from .efficiency import evaluate
from .calibration import calibrate
from .census import policy_census
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project

def qualify(subject, prior_defect, records, policy_generation, frontier_digest, now, dependency_states=(), parent_receipt=None):
    analyzed=[]
    realizations=[]
    outcomes=[]
    telemetry=[]
    for plan,outcome,regret in records:
        admit_realization(plan,outcome,policy_generation,frontier_digest,now)
        info=realize(plan,outcome,prior_defect)
        score=None if outcome.outcome not in {"PASS","FAIL"} else brier_score(plan.predicted_pass,outcome.outcome)
        eff=evaluate(plan,outcome,info.realized_gain)
        analyzed.append((plan.strategy,info,score if score is not None else 0,eff,regret))
        realizations.append(info); outcomes.append(outcome)
        telemetry.append(project(subject,plan,outcome,info,score,eff,regret))
    calibration=calibrate(realizations)
    census=policy_census(analyzed)
    status=standing(calibration,outcomes,dependency_states)
    receipt=manufacture_receipt(subject,policy_generation,frontier_digest,census,status,parent_receipt)
    return {"calibration":calibration,"census":census,"standing":status,"receipt":receipt,
            "telemetry":tuple(telemetry),"actuation_performed":False}
