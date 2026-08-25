from .errors import Refused

REQUIRED = frozenset("discovery conformance simulation prediction optimization intervention monitoring event_centric object_centric declarative_procedural powl".split())

def require(names):
    seen = frozenset(names)
    missing = REQUIRED - seen
    if missing:
        raise Refused("INCOMPLETE_METHODOLOGY_CLOSURE", ",".join(sorted(missing)))
    return seen
