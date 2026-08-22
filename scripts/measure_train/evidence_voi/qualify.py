from .calibration import admit_calibration
from .frontier import frontier_digest, admit_frontier
from .selector import select_measurements
from .intent import MeasurementIntent
from .standing import bounded_standing
from .receipt import manufacture_receipt

def qualify(subject,belief,candidates,calibrations,budget,now,proofs=(),strategy="MAX_INFORMATION_GAIN",dependency_standing="PARTIAL_ALIVE",expected_frontier=None):
    admitted=tuple(admit_calibration(c,next(x for x in calibrations if x.candidate_id==c.candidate_id),now) for c in candidates)
    digest=frontier_digest(candidates,admitted)
    if expected_frontier is not None:
        admit_frontier(expected_frontier,candidates,admitted)
    selected=select_measurements(belief,candidates,admitted,budget,proofs,strategy)
    intent=MeasurementIntent(subject,tuple(c.candidate_id for c in selected),digest,strategy)
    standing=bounded_standing(selected,dependency_standing)
    receipt=manufacture_receipt(intent,belief,selected,standing)
    telemetry=tuple({"activity":"select_measurement","repo":subject.repo,"sha":subject.sha,"candidate_id":c.candidate_id,"frontier":digest,"authority":"SELECT"} for c in selected)
    return {"intent":intent,"selected":selected,"standing":standing,"receipt":receipt,"telemetry":telemetry,"actuation_performed":False}
