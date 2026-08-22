from .calibration import estimate
from .cluster import validate_disjoint
from .admission import admit
from .sequential import sequential_test
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project
def qualify(subject,trials,witnesses,clusters,now,min_trials=4,min_independent_clusters=2,
            accept_log_lr=1.0,reject_log_lr=-1.0,parent_receipt=None):
    validate_disjoint(clusters)
    source_ids=sorted({s for c in clusters for s in c.source_ids})
    estimates=tuple(estimate(s,trials) for s in source_ids)
    admitted,under=admit(subject,witnesses,estimates,now,min_trials)
    seq=sequential_test(admitted,estimates,accept_log_lr,reject_log_lr)
    status=standing(admitted,under,seq,min_independent_clusters)
    receipt=manufacture_receipt(subject,estimates,seq,status,under,parent_receipt)
    return {"estimates":estimates,"witnesses":admitted,"undercalibrated":under,
            "sequential":seq,"standing":status,"receipt":receipt,
            "telemetry":project(subject,admitted,estimates,seq),"actuation_performed":False}
