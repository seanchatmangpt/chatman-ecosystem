from dataclasses import dataclass
from .epoch import ClosureEpoch
from .refusal import Refused

@dataclass(frozen=True)
class Trajectory:
    epochs: tuple[ClosureEpoch,...]
    def __post_init__(self):
        if len(self.epochs) < 2: raise Refused("INSUFFICIENT_TRAJECTORY")
        universe=self.epochs[0].universe
        for a,b in zip(self.epochs,self.epochs[1:]):
            if b.subject.generation != a.subject.generation+1: raise Refused("TORN_GENERATION")
            if b.observed_at <= a.observed_at: raise Refused("NONMONOTONE_TIME")
            if b.universe != universe: raise Refused("OBLIGATION_UNIVERSE_DRIFT")
    @property
    def current(self): return self.epochs[-1]
