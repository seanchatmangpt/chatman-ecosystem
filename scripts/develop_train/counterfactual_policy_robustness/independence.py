from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True, slots=True)
class EstimatorIdentity: name:str; implementation_digest:str; model_digest:str|None=None
@dataclass(frozen=True, slots=True)
class IndependenceProof: left:EstimatorIdentity; right:EstimatorIdentity; proven:bool
def require_independent(proof):
    if not proof.proven: raise Refused('REFUSED_INDEPENDENCE_UNPROVEN')
    if proof.left.implementation_digest == proof.right.implementation_digest: raise Refused('REFUSED_SHARED_IMPLEMENTATION')
    if proof.left.model_digest and proof.left.model_digest == proof.right.model_digest: raise Refused('REFUSED_SHARED_MODEL')
    return proof
