from dataclasses import dataclass
from .authority import ActionClass,admit
from .failure import combine_standing,require_failure_worlds
from .methodology import require_methodologies
from .engine import require_engine_correspondence
from .distribution import require_distribution
from .oracle import require_oracles
from .receipt import Receipt
@dataclass(frozen=True)
class Qualification:
    standing:str; receipt:Receipt|None
def qualify(subject,generation,mode,methodologies,engines,regions,oracles,failure_worlds,states,replay_root,now):
    require_methodologies(methodologies); require_engine_correspondence(engines); require_distribution(regions,now); require_oracles(oracles); require_failure_worlds(failure_worlds); admit(ActionClass.SELECT)
    standing=combine_standing(states)
    if standing=="BUILD_BROKEN": return Qualification(standing,None)
    return Qualification(standing,Receipt(subject.key,generation,mode,standing,replay_root))
