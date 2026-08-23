from enum import Enum
from .transport import Relation

class Recovery(str, Enum):
    STABLE="STABLE"; OBSERVABILITY_RECOVERED="OBSERVABILITY_RECOVERED"; SEMANTIC_REPAIR="SEMANTIC_REPAIR"; REGRESSED="REGRESSED"

def classify(previous: Relation, current: Relation) -> Recovery:
    if previous == Relation.CENSORED and current == Relation.EXACT: return Recovery.OBSERVABILITY_RECOVERED
    if previous == Relation.DIVERGED and current == Relation.EXACT: return Recovery.SEMANTIC_REPAIR
    if previous == Relation.EXACT and current in {Relation.DIVERGED, Relation.CENSORED}: return Recovery.REGRESSED
    return Recovery.STABLE
