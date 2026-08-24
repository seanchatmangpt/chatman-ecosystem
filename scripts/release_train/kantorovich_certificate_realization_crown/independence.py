from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class IndependenceWitness:
    implementations: int
    models: int
    roots: int
def witness(observations):
    w=IndependenceWitness(len({o.implementation for o in observations}),len({o.model for o in observations}),len({o.root for o in observations}))
    if min(w.implementations,w.models,w.roots) < 2: raise Refused("INSUFFICIENT_INDEPENDENCE")
    return w
