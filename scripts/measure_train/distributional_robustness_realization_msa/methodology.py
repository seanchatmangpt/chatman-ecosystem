from .refusal import Refused
REQUIRED=frozenset({"DISCOVERY","CONFORMANCE","SIMULATION","PREDICTION","OPTIMIZATION","INTERVENTION","MONITORING","EVENT_CENTRIC","OBJECT_CENTRIC","DECLARATIVE","PROCEDURAL"})
def coverage(kinds):
    present=frozenset(kinds); missing=tuple(sorted(REQUIRED-present))
    return {"present":tuple(sorted(present&REQUIRED)),"missing":missing,"complete":not missing}
def require_complete(kinds):
    result=coverage(kinds)
    if not result["complete"]: raise Refused("REFUSED[INCOMPLETE_METHODOLOGY_COVERAGE]")
    return result
