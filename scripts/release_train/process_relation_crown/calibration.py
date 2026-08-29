from dataclasses import dataclass
from .relation import Relation
from .refusal import Refused
from .bounds import confidence_interval
@dataclass(frozen=True)
class RelationCalibration:
    relation:Relation; generation:int; digest:str; support:int; false_equivalence:int; false_refusal:int; cost:float
    def __post_init__(self):
        if self.generation<0 or len(self.digest)!=64: raise Refused("MALFORMED_CALIBRATION_ID")
        if self.support<=0 or min(self.false_equivalence,self.false_refusal)<0: raise Refused("INVALID_CALIBRATION_COUNTS")
        if self.false_equivalence+self.false_refusal>self.support: raise Refused("INVALID_CALIBRATION_COUNTS")
        if self.cost<0: raise Refused("INVALID_CALIBRATION_COST")
    @property
    def fe_upper(self): return confidence_interval(self.false_equivalence,self.support)[1]
    @property
    def fr_upper(self): return confidence_interval(self.false_refusal,self.support)[1]
