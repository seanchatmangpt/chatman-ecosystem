from .observation import METHODS
from .subject import Refused
def coverage(observations):
    present={o.methodology for o in observations}
    missing=tuple(sorted(METHODS-present))
    return {"present":tuple(sorted(present)),"missing":missing,"complete":not missing}
def require_complete(observations):
    c=coverage(observations)
    if not c["complete"]: raise Refused("REFUSED[INCOMPLETE_METHODOLOGY_COVERAGE]")
    return c
