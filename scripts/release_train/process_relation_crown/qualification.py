from dataclasses import dataclass
from .admission import admit,Thresholds
from .frontier import CalibrationFrontier
from .oracle import require_independent
from .selector import Strategy,select
from .standing import compute
from .receipt import Receipt
from .rails import require_rails
from .methodology import require_complete as require_methods
from .failures import require_complete as require_failures
@dataclass(frozen=True)
class Qualification:
    standing:str; selected:object; receipt:object
def qualify(*,subject,row,frontier:CalibrationFrontier,metamorphic,oracles,candidates,strategy:Strategy,rails,required_relation,methodologies,failure_worlds,blockers=()):
    frontier.require(row); admit(row,metamorphic,Thresholds())
    require_independent(*oracles); require_rails(rails,subject.canonical,required_relation)
    require_methods(methodologies); require_failures(failure_worlds)
    standing=compute(blockers=blockers,calibrated=True)
    if blockers: return Qualification(standing.value,None,None)
    chosen=select(candidates,strategy)
    receipt=Receipt(subject.canonical,required_relation.value,row.digest,strategy.value,standing.value)
    return Qualification(standing.value,chosen,receipt)
