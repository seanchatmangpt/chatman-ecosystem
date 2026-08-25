from .refusal import Refused

REQUIRED = {"DISCOVERY", "CONFORMANCE", "SIMULATION", "PREDICTION", "OPTIMIZATION", "INTERVENTION", "MONITORING", "EVENT_CENTRIC", "OBJECT_CENTRIC", "DECLARATIVE", "PROCEDURAL"}

def require_methods(observations):
    present = {observation.methodology for observation in observations}
    missing = tuple(sorted(REQUIRED - present))
    if missing:
        raise Refused("INCOMPLETE_METHODOLOGY_COVERAGE")
    return tuple(sorted(present))
