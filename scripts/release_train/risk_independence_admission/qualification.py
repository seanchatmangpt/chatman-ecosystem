from dataclasses import dataclass
from .decision import decide,Decision
from .dependence import require_dependence_bounds
from .composition import compose
from .methodology import require_methodologies
from .correspondence import require_engines,require_rails
from .distribution import require_distribution
from .failures import require_failure_worlds
from .standing import compute
from .receipt import manufacture
from .errors import Refused
@dataclass(frozen=True)
class Qualification:
    decision:object; interval:object; standing:object; receipt:object
def qualify(*,subject,evidence,losses,calibration,frontier,ancestry_pair,pair_overlap,higher_overlap,max_pair,max_higher,candidate_intervals,methodologies,engines,rails,hosts,now,max_age_seconds,failure_worlds,blocked=False,failed=False):
    frontier.require(calibration.generation,calibration.digest)
    if not calibration.admitted(8,'1/10','1/10','1/2'): raise Refused('DECISION_CALIBRATION_NOT_ADMITTED')
    ancestry,a,b=ancestry_pair; ancestry.require_disjoint(a,b)
    require_dependence_bounds(pair_overlap,higher_overlap,max_pair,max_higher)
    result=decide(evidence,losses)
    interval=compose(*candidate_intervals,result.decision)
    require_methodologies(methodologies); require_engines(engines); require_rails(rails); require_distribution(hosts,now,max_age_seconds); require_failure_worlds(failure_worlds)
    standing=compute(failed=failed,blocked=blocked,deferred=result.decision==Decision.DEFER,qualified=True)
    if standing.value not in ('PARTIAL_ALIVE',): return Qualification(result,None,standing,None)
    mode='INDEPENDENT_PRODUCT' if result.decision==Decision.INDEPENDENT else 'CONSERVATIVE_FRECHET'
    rec=manufacture(subject=subject.exact,calibration_generation=calibration.generation,calibration_digest=calibration.digest,decision=result.decision.value,composition_mode=mode,standing=standing.value,blockers=())
    return Qualification(result,interval,standing,rec)
