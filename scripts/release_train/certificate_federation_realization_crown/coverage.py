from .transport import Observation, TransportState
from .refusal import Refused

def require_transport_coverage(observations: tuple[Observation,...], minimum: int=2) -> tuple[str,...]:
    resolved=[o for o in observations if o.state == TransportState.RESOLVED]
    identities={(o.implementation,o.model,o.domain) for o in resolved}
    if len(resolved) < minimum: raise Refused("INSUFFICIENT_RESOLVED_TRANSPORTS")
    if len(identities) < minimum: raise Refused("PSEUDO_INDEPENDENT_TRANSPORTS")
    return tuple(sorted(o.transport_id for o in resolved))
