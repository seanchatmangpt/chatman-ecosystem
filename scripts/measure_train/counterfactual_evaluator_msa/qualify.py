import hashlib,json
from collections import defaultdict
from .admission import admit_cases
from .calibration import calibrate
from .frontier import CalibrationModel,current_frontier
from .weights import weight_diagnostics
from .sensitivity import sensitivity_profile
from .admit_estimator import admit_estimator
from .consensus import estimator_consensus
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project

def qualify(subject,cases,model_specs,proofs,now,dependency_standings=()):
    admitted=admit_cases(subject,cases,now)
    by_est=defaultdict(list)
    for c in admitted: by_est[c.estimator.estimator_id].append(c)
    models=[]; ids=[]; estimates=[]; census=[]
    for estimator_id,generation,digest,identity,perturbed in model_specs:
        own=tuple(by_est[estimator_id]); cal=calibrate(estimator_id,own)
        model=CalibrationModel(estimator_id,generation,digest,cal); models.append(model)
        ids.append(identity); estimates.append(sum((c.estimate for c in own),start=0)/len(own) if own else 0)
    frontier=current_frontier(models)
    for model,(_,_,_,identity,perturbed) in zip(models,model_specs):
        own=tuple(by_est[model.estimator_id]); wd=weight_diagnostics(own)
        base=sum((c.estimate for c in own),start=0)/len(own) if own else 0
        sens=sensitivity_profile(base,perturbed)
        admit_estimator(model,frontier,wd,sens)
        census.append({"estimator_id":model.estimator_id,"family":identity.family,"support":model.calibration.support,"mae":str(model.calibration.mae),"ess":str(wd.ess),"max_to_mean":str(wd.max_to_mean),"sensitivity":str(sens.max_shift)})
    consensus=estimator_consensus(estimates,ids,proofs)
    status=standing(consensus["state"],tuple("PASS" for _ in models),dependency_standings)
    frontier_payload=[(m.estimator_id,m.generation,m.digest) for m in frontier]
    fd=hashlib.sha256(json.dumps(frontier_payload,separators=(",",":")).encode()).hexdigest()
    receipt=manufacture_receipt(subject,fd,consensus,census,status)
    return {"frontier":frontier,"consensus":consensus,"census":tuple(census),"standing":status,"receipt":receipt,"telemetry":project(subject,admitted,models,status),"actuation_performed":False}
