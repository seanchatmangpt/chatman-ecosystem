from enum import Enum
class Relation(str,Enum):
    EXACT="EXACT"; STUTTER="STUTTER"; PARTIAL_ORDER="PARTIAL_ORDER"; ACTIVITY="ACTIVITY"
# Strength is a partial order: STUTTER and PARTIAL_ORDER are intentionally incomparable.
def discharges(proved:Relation, required:Relation)->bool:
    if proved==required: return True
    if proved==Relation.EXACT: return True
    if required==Relation.ACTIVITY and proved in {Relation.STUTTER,Relation.PARTIAL_ORDER}: return True
    return False
