from .errors import Refused

REQUIRED = frozenset({
    "discovery","conformance","simulation","prediction","optimization",
    "intervention","monitoring","event_centric","object_centric",
    "declarative_procedural","powl",
})


def require_complete(observations):
    seen = {item.methodology for item in observations}
    missing = REQUIRED - seen
    if missing:
        raise Refused("INCOMPLETE_CERTIFICATE_METHODOLOGY_CLOSURE", ",".join(sorted(missing)))
    return frozenset(seen)
