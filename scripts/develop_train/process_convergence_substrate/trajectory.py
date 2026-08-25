from dataclasses import dataclass
from .epoch import ClosureEpoch
from .refusal import Refused

@dataclass(frozen=True)
class Trajectory:
    epochs: tuple[ClosureEpoch, ...]

    def __post_init__(self):
        if len(self.epochs) < 2:
            raise Refused("INSUFFICIENT_TRAJECTORY")
        universe=set(self.epochs[0].by_key())
        prev=self.epochs[0]
        for cur in self.epochs[1:]:
            if cur.subject.generation != prev.subject.generation + 1:
                raise Refused("TORN_GENERATION")
            if cur.at <= prev.at:
                raise Refused("TIME_REVERSAL")
            if set(cur.by_key()) != universe:
                raise Refused("OBLIGATION_UNIVERSE_DRIFT")
            prev=cur

    @property
    def current(self):
        return self.epochs[-1]
