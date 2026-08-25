from dataclasses import dataclass
from .admission import admit
from .selection import select
from .topology import METHODS,RAILS,FAILURES,require_complete
from .engine import require_differential
from .distributed import require_current_tls
from .reactor import require_correspondence
from .standing import combine
from .receipt import Receipt
@dataclass(frozen=True)
class Qualification:
    standing:str; selected:object; receipt:object
def qualify(subject, calibrations, sensitivities, strategy, methods, rails, failures, engines, regions, reactor, dependency_states=(), blockers=()):
    good=[]
    for c in calibrations:
        admit(c,sensitivities[c.mode]); good.append(c)
    selected=select(good,strategy)
    require_complete(methods,METHODS,"INCOMPLETE_METHODOLOGY")
    require_complete(rails,RAILS,"INCOMPLETE_RAILS")
    require_complete(failures,FAILURES,"INCOMPLETE_FAILURE_WORLDS")
    require_differential(engines)
    require_current_tls(regions,selected.generation)
    require_correspondence(reactor,subject.semantic_digest,engines[0].trace_digest)
    standing=combine(tuple(dependency_states) or ("PARTIAL_ALIVE",),blockers)
    receipt=None if standing in {"BUILD_BROKEN","BLOCKED"} else Receipt(subject.key,selected.generation,strategy,selected.mode,standing,tuple(blockers))
    return Qualification(standing,selected,receipt)
