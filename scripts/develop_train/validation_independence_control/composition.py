from enum import Enum
from .errors import Refused
from .dependence import effective_independence
from .validator import require_distinct_validators
class CompositionMode(str,Enum):
    CONSERVATIVE="CONSERVATIVE"
    INDEPENDENCE_QUALIFIED="INDEPENDENCE_QUALIFIED"
def compose(a_interval,b_interval,mode,*,graph=None,a_validator=None,b_validator=None,dependence=None):
    if mode==CompositionMode.CONSERVATIVE:
        return a_interval.conservative_and(b_interval)
    if mode!=CompositionMode.INDEPENDENCE_QUALIFIED:
        raise Refused("UNKNOWN_COMPOSITION_MODE")
    if None in (graph,a_validator,b_validator,dependence):
        raise Refused("MISSING_INDEPENDENCE_EVIDENCE")
    require_distinct_validators(a_validator,b_validator)
    effective_independence(graph,a_validator.evidence_id,b_validator.evidence_id,a_validator.provenance,b_validator.provenance,dependence)
    return a_interval.independent_and(b_interval)
