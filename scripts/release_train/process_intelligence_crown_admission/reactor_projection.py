from dataclasses import dataclass
from enum import Enum
from .identity import digest64
from .refusal import require

class Engine(str, Enum):
    REACTOR="REACTOR"; BEAM="BEAM"; PLAN="PLAN"; WASM="WASM"; NIF="NIF"; REMOTE="REMOTE"

@dataclass(frozen=True)
class Projection:
    engine: Engine
    semantic_digest: str
    obligations: frozenset[str]
    artifact_digest: str

    def __post_init__(self):
        digest64(self.semantic_digest); digest64(self.artifact_digest)
        require(bool(self.obligations), "EMPTY_PROJECTION_OBLIGATIONS")

def require_correspondence(a: Projection, b: Projection) -> None:
    require(a.semantic_digest == b.semantic_digest, "SEMANTIC_DIGEST_DIVERGENCE")
    require(a.obligations == b.obligations, "PROJECTION_OBLIGATION_LOSS")
    require(a.engine != b.engine, "NON_INDEPENDENT_ENGINE_PAIR")
