from .subject import Refused

REQUIRED = {"DISCOVERY", "CONFORMANCE", "SIMULATION", "PREDICTION", "OPTIMIZATION", "INTERVENTION", "MONITORING", "EVENT_CENTRIC", "OBJECT_CENTRIC", "DECLARATIVE", "PROCEDURAL"}

def require(methods):
    missing = REQUIRED - set(methods)
    if missing:
        raise Refused("REFUSED[INCOMPLETE_METHODOLOGY_COVERAGE]")
    return True
