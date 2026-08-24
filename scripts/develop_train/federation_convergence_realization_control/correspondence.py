from .errors import Refused
def require_correspondence(observations):
    if len({o.engine for o in observations})<2: raise Refused("INSUFFICIENT_ENGINE_CORRESPONDENCE")
    if len({o.region for o in observations})<2: raise Refused("INSUFFICIENT_REGION_CORRESPONDENCE")
    if len({o.evidence_root for o in observations})<2: raise Refused("INSUFFICIENT_EVIDENCE_ROOTS")
    return True
