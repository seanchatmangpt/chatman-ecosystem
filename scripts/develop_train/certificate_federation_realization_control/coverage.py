from .errors import Refused
from .observation import TransportState

def require_transport_coverage(observations, minimum_distinct=2):
    resolved = [o for o in observations if o.state == TransportState.RESOLVED]
    ids = {o.transport_id for o in resolved}
    provenance = {(o.implementation,o.model,o.domain) for o in resolved}
    if len(ids) < minimum_distinct or len(provenance) < minimum_distinct:
        raise Refused("INSUFFICIENT_INDEPENDENT_TRANSPORT_COVERAGE")
    return frozenset(ids)
