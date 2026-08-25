from enum import Enum
from .observation import Relation

class Recovery(str, Enum):
    NONE = "NONE"
    OBSERVABILITY_RECOVERED = "OBSERVABILITY_RECOVERED"
    SEMANTIC_REPAIR = "SEMANTIC_REPAIR"
    SEMANTIC_REGRESSION = "SEMANTIC_REGRESSION"

def classify(previous: Relation, current: Relation) -> Recovery:
    if previous == Relation.CENSORED and current in {Relation.EXACT, Relation.ADVANCED}:
        return Recovery.OBSERVABILITY_RECOVERED
    if previous == Relation.DIVERGED and current in {Relation.EXACT, Relation.ADVANCED}:
        return Recovery.SEMANTIC_REPAIR
    if previous in {Relation.EXACT, Relation.ADVANCED} and current == Relation.DIVERGED:
        return Recovery.SEMANTIC_REGRESSION
    return Recovery.NONE
