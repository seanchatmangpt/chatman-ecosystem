from .errors import Refused
REQUIRED=frozenset({"discovery","conformance","simulation","prediction","optimization","intervention","monitoring","event-centric","object-centric","declarative","procedural"})
def require_methodologies(observations):
    if REQUIRED-{o.methodology for o in observations}: raise Refused("INCOMPLETE_METHODOLOGY_CLOSURE")
    return True
