from .subject import Refused
REQUIRED={"DISCOVERY","CONFORMANCE","SIMULATION","PREDICTION","OPTIMIZATION","INTERVENTION","MONITORING","EVENT_CENTRIC","OBJECT_CENTRIC","DECLARATIVE","PROCEDURAL"}
def methodology_coverage(kinds):
    present=set(kinds)
    missing=tuple(sorted(REQUIRED-present))
    return {"present":tuple(sorted(present & REQUIRED)),"missing":missing,"complete":not missing}
def require_complete(kinds):
    c=methodology_coverage(kinds)
    if not c["complete"]: raise Refused("REFUSED[INCOMPLETE_METHODOLOGY_COVERAGE]")
    return c
