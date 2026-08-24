from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Trajectory:
    observations: tuple
    @classmethod
    def build(cls, observations):
        obs=tuple(observations)
        gens=[o.generation for o in obs]
        if gens != sorted(gens): raise Refused("NON_MONOTONE_GENERATION")
        if any(b-a != 1 for a,b in zip(gens,gens[1:])): raise Refused("TORN_GENERATION")
        if len({o.semantic_digest for o in obs}) != 1: raise Refused("FOREIGN_SEMANTIC_SUBJECT")
        times=[o.observed_at for o in obs]
        if any(b <= a for a,b in zip(times,times[1:])): raise Refused("NON_MONOTONE_TIME")
        return cls(obs)
    @property
    def head(self): return self.observations[-1]
