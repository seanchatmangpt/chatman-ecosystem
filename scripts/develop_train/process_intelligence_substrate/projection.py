from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from .errors import Refused

class Engine(str, Enum):
    BEAM="BEAM"; PLAN="PLAN"; WASM="WASM"; NIF="NIF"; REMOTE="REMOTE"

@dataclass(frozen=True)
class Projection:
    engine: Engine
    semantic_digest: str
    obligations: frozenset[str]

    def __post_init__(self) -> None:
        if len(self.semantic_digest) != 64:
            raise Refused("PROJECTION_DIGEST")

    def identity(self) -> str:
        payload = self.engine.value + self.semantic_digest + "|".join(sorted(self.obligations))
        return sha256(payload.encode()).hexdigest()


def correspondence(a: Projection, b: Projection) -> frozenset[str]:
    if a.semantic_digest != b.semantic_digest:
        raise Refused("SEMANTIC_DIGEST_DIVERGENCE")
    lost = a.obligations ^ b.obligations
    if lost:
        raise Refused("PROJECTION_OBLIGATION_LOSS", ",".join(sorted(lost)))
    return a.obligations
