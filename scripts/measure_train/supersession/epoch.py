from dataclasses import dataclass
from datetime import datetime
from .subject import Refused

@dataclass(frozen=True, order=True)
class Epoch:
    observed_at: datetime
    sequence: int

    def __post_init__(self):
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_EPOCH]")
        if self.sequence < 0:
            raise Refused("REFUSED[INVALID_EPOCH_SEQUENCE]")
