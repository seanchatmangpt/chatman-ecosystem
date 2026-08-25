from .errors import Refused

REQUIRED = frozenset({"discovery", "conformance", "simulation", "prediction", "optimization", "intervention", "monitoring", "event-centric", "object-centric", "declarative", "procedural"})


def require_methodologies(values):
    if REQUIRED - set(values):
        raise Refused("INCOMPLETE_METHODOLOGY_CLOSURE")
    return True
