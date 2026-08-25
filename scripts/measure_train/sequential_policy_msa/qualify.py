from .trajectory import admit_trajectory
from .information import cumulative_information,efficiency
from .budget import budget_state
from .calibration import forecast_calibration
from .change_detection import page_hinkley
from .admission import admit_current
from .standing import standing
from .receipt import manufacture_receipt

def qualify(subject,policy,steps,current_policy,now,budget,dependency_states=(),parent_receipt=None,
            min_support=3,max_mae=None):
    admitted=admit_trajectory(subject,policy,steps)
    calibration=forecast_calibration(admitted,min_support=min_support) if max_mae is None else forecast_calibration(admitted,min_support,max_mae)
    drift=page_hinkley(admitted)
    admission=admit_current(subject,policy,admitted,current_policy,now,calibration,drift)
    predicted,realized,error=cumulative_information(admitted)
    resources=budget_state(admitted,budget)
    status=standing(admitted,resources,calibration["state"],dependency_states)
    census={"admission":admission,"predicted_bits":str(predicted),"realized_bits":str(realized),
            "forecast_error_bits":str(error),"resources":{k:str(v) for k,v in resources.items()},
            "calibration":{k:str(v) for k,v in calibration.items()},
            "drift":{k:str(v) for k,v in drift.items()},"efficiency":{k:str(v) for k,v in efficiency(admitted).items()}}
    receipt=manufacture_receipt(subject,policy,census,status,parent_receipt)
    telemetry=tuple({"activity":"measure_sequential_policy","repo":subject.repo,"sha":subject.sha,
                     "policy":policy.policy_id,"generation":policy.generation,"step":s.step,
                     "predicted_bits":str(s.predicted_bits),"realized_bits":str(s.realized_bits),
                     "outcome":s.outcome,"evidence_id":s.evidence_id,"time":s.observed_at.isoformat()}
                    for s in admitted)
    return {"standing":status,"census":census,"receipt":receipt,"telemetry":telemetry,
            "actuation_performed":False}
