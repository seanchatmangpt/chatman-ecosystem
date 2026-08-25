from .errors import Refused

REQUIRED = frozenset({
    "discovery", "conformance", "simulation", "prediction", "optimization",
    "intervention", "monitoring", "event_centric", "object_centric",
    "declarative", "procedural",
})

def require_methodologies(methodologies):
    missing = REQUIRED - set(methodologies)
    if missing:
        raise Refused("INCOMPLETE_METHODOLOGY_CLOSURE")
    return True
