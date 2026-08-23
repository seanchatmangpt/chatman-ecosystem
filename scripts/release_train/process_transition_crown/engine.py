from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True)
class EngineWitness:
    engine: str
    semantic_digest: str
    obligations: tuple[str,...]
    trace_digest: str


def require_equivalent(witnesses: tuple[EngineWitness,...]) -> tuple[EngineWitness,...]:
    if len({w.engine for w in witnesses}) < 2:
        raise Refused("INSUFFICIENT_ENGINE_DIVERSITY")
    if len({w.semantic_digest for w in witnesses}) != 1:
        raise Refused("ENGINE_SEMANTIC_DIVERGENCE")
    if len({w.obligations for w in witnesses}) != 1:
        raise Refused("ENGINE_OBLIGATION_DIVERGENCE")
    if len({w.trace_digest for w in witnesses}) != 1:
        raise Refused("ENGINE_TRACE_DIVERGENCE")
    return witnesses
