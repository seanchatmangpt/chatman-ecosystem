from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class IndependenceWitness:
    implementations: frozenset[str]
    models: frozenset[str]
    evidence_roots: frozenset[str]

    @property
    def admitted(self) -> bool:
        return len(self.implementations) >= 2 and len(self.models) >= 2 and len(self.evidence_roots) >= 2


def witness(observations) -> IndependenceWitness:
    obs = tuple(observations)
    result = IndependenceWitness(
        frozenset(item.validator_implementation for item in obs),
        frozenset(item.validator_model for item in obs),
        frozenset(item.evidence_root for item in obs),
    )
    if not result.admitted:
        raise Refused("INSUFFICIENT_ORACLE_INDEPENDENCE")
    return result
