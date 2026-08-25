from dataclasses import dataclass
from .calibration import RelationCalibration
from .relation import Relation
from .refusal import Refused
@dataclass(frozen=True)
class CalibrationFrontier:
    rows:tuple[RelationCalibration,...]
    def current(self,relation:Relation)->RelationCalibration:
        rs=[r for r in self.rows if r.relation==relation]
        if not rs: raise Refused("CALIBRATION_MISSING")
        g=max(r.generation for r in rs); top=[r for r in rs if r.generation==g]
        if len({r.digest for r in top})!=1: raise Refused("DIVERGENT_CALIBRATION_FRONTIER")
        return top[0]
    def require(self,row:RelationCalibration):
        cur=self.current(row.relation)
        if (row.generation,row.digest)!=(cur.generation,cur.digest): raise Refused("STALE_CALIBRATION")
        return cur
