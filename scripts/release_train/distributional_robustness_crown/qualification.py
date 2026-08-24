import hashlib,json
from .calibration import current
from .methodology import require_methods
from .correspondence import require_engines,require_oracles
from .topology import require_regions
from .failures import require_complete
from .dependency import blockers
from .standing import bounded_standing
from .receipt import Receipt
from .realization import realization_metrics,monotone_stress
def qualify(*,subject,calibrations,realizations,methods,engines,oracles,regions,current_generation,worlds,dependency_graph,dependency_standing):
    cal=current(calibrations); metrics=realization_metrics(realizations)
    require_methods(methods); require_engines(engines); require_oracles(oracles); require_regions(regions,current_generation); require_complete(worlds)
    bs=blockers(dependency_graph,dependency_standing)
    realized=(metrics["false_stable"]==0 and metrics["mae"]<=cal.miss_rate and monotone_stress(realizations))
    standing=bounded_standing(calibrated=cal.support>=2,realized=realized,methods=True,engines=True,oracles=True,regions=True,failures=True,blockers=bs)
    if standing=="BUILD_BROKEN": return standing,None
    evidence=hashlib.sha256(json.dumps({"cal":cal.digest,"metrics":metrics,"generation":subject.generation},sort_keys=True).encode()).hexdigest()
    return standing,Receipt.issue(subject.identity,standing,evidence)
