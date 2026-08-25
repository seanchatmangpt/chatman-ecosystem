from .errors import Refused
from .observation import TransportState

def require_engine_region_correspondence(observations):
    resolved = [o for o in observations if o.state == TransportState.RESOLVED]
    engines = {o.engine for o in resolved}
    regions = {o.region for o in resolved}
    roots = {o.evidence_root for o in resolved}
    if len(engines) < 2:
        raise Refused("INSUFFICIENT_ENGINE_CORRESPONDENCE")
    if len(regions) < 2:
        raise Refused("INSUFFICIENT_REGION_CORRESPONDENCE")
    if len(roots) < 2:
        raise Refused("INSUFFICIENT_EVIDENCE_ROOTS")
    return True
