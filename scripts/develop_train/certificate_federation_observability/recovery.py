from enum import Enum
from .observation import Relation
class Recovery(str,Enum): NONE="NONE"; OBSERVABILITY_RECOVERED="OBSERVABILITY_RECOVERED"; SEMANTIC_REPAIR="SEMANTIC_REPAIR"; REGRESSION="REGRESSION"
def classify(before,after):
    if before.relation==Relation.CENSORED and after.relation in {Relation.EXACT,Relation.ADVANCED}: return Recovery.OBSERVABILITY_RECOVERED
    if before.relation==Relation.DIVERGED and after.relation in {Relation.EXACT,Relation.ADVANCED}: return Recovery.SEMANTIC_REPAIR
    if before.relation in {Relation.EXACT,Relation.ADVANCED} and after.relation==Relation.DIVERGED: return Recovery.REGRESSION
    return Recovery.NONE
