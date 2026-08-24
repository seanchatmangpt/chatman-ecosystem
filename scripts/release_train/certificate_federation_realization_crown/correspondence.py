from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True)
class EngineWitness:
    engine: str
    implementation: str
    model: str
    semantic_digest: str
    trace_digest: str
    obligation_digest: str

def require_engine_correspondence(witnesses: list[EngineWitness], minimum: int=2) -> tuple[str,...]:
    if len(witnesses) < minimum: raise Refused("INSUFFICIENT_ENGINE_WITNESSES")
    if len({(w.implementation,w.model) for w in witnesses}) < minimum:
        raise Refused("PSEUDO_INDEPENDENT_ENGINES")
    signatures={(w.semantic_digest,w.trace_digest,w.obligation_digest) for w in witnesses}
    if len(signatures) != 1: raise Refused("ENGINE_CORRESPONDENCE_DIVERGENCE")
    return tuple(sorted(w.engine for w in witnesses))
