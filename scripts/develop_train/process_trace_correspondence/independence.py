from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Independence:
    pairs:frozenset[frozenset[str]]
    @classmethod
    def from_pairs(cls,pairs):
        out=set()
        for a,b in pairs:
            if not a or not b or a==b: raise Refused("INVALID_INDEPENDENCE")
            out.add(frozenset((a,b)))
        return cls(frozenset(out))
    def independent(self,a,b): return a!=b and frozenset((a,b)) in self.pairs
