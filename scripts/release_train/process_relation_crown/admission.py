from dataclasses import dataclass
from .calibration import RelationCalibration
from .metamorphic import MetamorphicWitness
from .refusal import Refused
@dataclass(frozen=True)
class Thresholds:
    min_support:int=20; max_fe_upper:float=.10; max_fr_upper:float=.20
def admit(row:RelationCalibration,witness:MetamorphicWitness,t:Thresholds=Thresholds()):
    witness.require()
    if row.support<t.min_support: raise Refused("CALIBRATION_UNDER_SUPPORTED")
    if row.fe_upper>t.max_fe_upper: raise Refused("FALSE_EQUIVALENCE_RISK")
    if row.fr_upper>t.max_fr_upper: raise Refused("FALSE_REFUSAL_RISK")
    return row
