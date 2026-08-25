from dataclasses import dataclass
from .currentness import current_frontier
from .methodology import require_closure
from .standing import combine
from .receipt import Receipt
@dataclass(frozen=True)
class Qualification:
    standing:str; generation:int; receipt:Receipt|None

def qualify(nodes, methodologies, states, selector='PARETO_REALIZED'):
    generation,current=current_frontier(nodes)
    require_closure(methodologies)
    standing=combine(states)
    if standing in {'BUILD_BROKEN','UNSUPPORTED'}: return Qualification(standing,generation,None)
    if standing=='ALIVE': standing='PARTIAL_ALIVE'
    r=Receipt(current[0].subject.key,generation,standing,tuple(n.evidence_id for n in current),selector)
    return Qualification(standing,generation,r)
