from dataclasses import dataclass
from .errors import Refused
from .vector_clock import VectorClock

@dataclass(frozen=True)
class Mutation:
    replica: str
    subject: str
    from_generation: int
    to_generation: int
    value_digest: str
    clock: VectorClock

    def __post_init__(self):
        if self.to_generation != self.from_generation + 1:
            raise Refused("NON_MONOTONE_GENERATION")
        if len(self.value_digest) != 64:
            raise Refused("INVALID_VALUE_DIGEST")
