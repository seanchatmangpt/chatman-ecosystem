from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused
@dataclass(frozen=True)
class ReplicaUniverse:
    members: tuple
    @classmethod
    def from_ids(cls,ids):
        ids=tuple(ids)
        if not ids or any(not x for x in ids) or len(set(ids))!=len(ids): raise Refused("REFUSED[INVALID_REPLICA_UNIVERSE]")
        return cls(tuple(sorted(ids)))
    def coverage(self,observations):
        seen={o.replica_id for o in observations}
        if not seen<=set(self.members): raise Refused("REFUSED[FOREIGN_REPLICA]")
        return Fraction(len(seen),len(self.members))
    def quorum_size(self): return len(self.members)//2+1
