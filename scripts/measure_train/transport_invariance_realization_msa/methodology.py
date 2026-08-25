from .refusal import Refused
REQUIRED={"DISCOVERY","CONFORMANCE","SIMULATION","PREDICTION","OPTIMIZATION","INTERVENTION","MONITORING","EVENT_CENTRIC","OBJECT_CENTRIC","DECLARATIVE","PROCEDURAL"}
def require_methods(cases):
    present={c.methodology for c in cases}; missing=REQUIRED-present
    if missing: raise Refused("REFUSED[INCOMPLETE_METHODOLOGY_COVERAGE]:"+",".join(sorted(missing)))
    return tuple(sorted(present))
