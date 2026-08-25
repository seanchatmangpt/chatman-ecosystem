from .refusal import Refused
REQUIRED={"DISCOVERY","CONFORMANCE","SIMULATION","PREDICTION","OPTIMIZATION","INTERVENTION","MONITORING","EVENT_CENTRIC","OBJECT_CENTRIC","DECLARATIVE","PROCEDURAL"}
def coverage(methods):
    present=set(methods); missing=tuple(sorted(REQUIRED-present)); return {"present":tuple(sorted(present & REQUIRED)),"missing":missing,"complete":not missing}
def require_complete(methods):
    c=coverage(methods)
    if not c["complete"]: raise Refused("REFUSED[INCOMPLETE_METHODOLOGY_COVERAGE]")
    return c
