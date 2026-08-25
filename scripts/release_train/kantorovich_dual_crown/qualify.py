import hashlib,json
from .certificate import verify_certificate
from .differential import require_independent
from .methodologies import require_methods
from .engines import require_engines
from .oracles import require_oracles
from .regions import require_regions
from .failures import require_failures
from .standing import compute,Qualification
from .receipt import make
def qualify(*,subject,source,target,metric,plan,dual,oracle_a,oracle_b,ambiguity,robust,calibration,methods,engines,oracles,regions,failures,dependency_blockers=()):
    cert=verify_certificate(source,target,metric,plan,dual)
    gap=require_independent(oracle_a,oracle_b)
    require_methods(methods); require_engines(engines); require_oracles(oracles); require_regions(regions); require_failures(failures)
    calibrated=(calibration.current and calibration.generation==subject.generation and calibration.miss_rate<=ambiguity.radius and robust.radius==ambiguity.radius)
    q=compute(blockers=dependency_blockers,certificate=(gap==0 and cert.primal_cost==cert.dual_value),calibrated=calibrated,global_ok=True)
    if q.standing in {"BUILD_BROKEN","BLOCKED"}: return q,None
    evidence={"cost":str(cert.primal_cost),"gap":str(gap),"kind":ambiguity.kind,"generation":subject.generation,"witness":robust.witness_digest}
    ed=hashlib.sha256(json.dumps(evidence,sort_keys=True).encode()).hexdigest()
    q=Qualification(q.standing,q.blockers,ed)
    return q,make(f"{subject.repo}@{subject.sha}#{subject.semantic}",q.standing,ed)
