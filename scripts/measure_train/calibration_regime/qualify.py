from .distance import model_distance, classify_distance
from .frontier import resolve_frontier
from .admission import admit_current_model
from .standing import bounded_standing
from .receipt import manufacture_receipt

def qualify(subject, source_id, reference_model, versions, outcomes, now, threshold, dependency_standings=(), parent_receipt=None):
    frontier=resolve_frontier(versions)
    current=frontier["current"]
    vector=model_distance(reference_model,current.model)
    drift_state=classify_distance(reference_model,current.model,threshold)
    admission=admit_current_model(current.model,frontier,drift_state,now)
    standing=bounded_standing(outcomes,drift_state,dependency_standings)
    receipt=manufacture_receipt(subject,source_id,current.model,current.generation,vector,drift_state,standing,parent_receipt)
    telemetry={"activity":"measure_calibration_regime","repo":subject.repo,"sha":subject.sha,"source_id":source_id,
               "model_id":current.model.model_id,"generation":current.generation,"drift_state":drift_state,
               "standing":standing,"time":now.isoformat()}
    return {"admission":admission,"frontier":frontier,"drift":vector,"drift_state":drift_state,
            "standing":standing,"receipt":receipt,"telemetry":telemetry,"actuation_performed":False}
