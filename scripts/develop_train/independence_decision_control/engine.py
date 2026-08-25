from dataclasses import dataclass

from .errors import Refused


@dataclass(frozen=True)
class EngineWitness:
    engine: str
    implementation: str
    semantic_digest: str
    trace_digest: str
    obligation_digest: str


def require_correspondence(witnesses):
    if len({witness.implementation for witness in witnesses}) < 2:
        raise Refused("ENGINE_ALIAS")
    for attribute in ("semantic_digest", "trace_digest", "obligation_digest"):
        if len({getattr(witness, attribute) for witness in witnesses}) != 1:
            raise Refused("ENGINE_DIVERGENCE")
    return True
