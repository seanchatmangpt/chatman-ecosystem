from .errors import Refused

REQUIRED = frozenset({
    "discovery","conformance","simulation","prediction","optimization",
    "intervention","monitoring","event_centric","object_centric",
    "declarative_procedural","powl",
})

def require_methodologies(observations):
    seen = {o.methodology for o in observations}
    missing = REQUIRED - seen
    if missing:
        raise Refused("INCOMPLETE_METHODOLOGY_CLOSURE", ",".join(sorted(missing)))
    return frozenset(seen)
