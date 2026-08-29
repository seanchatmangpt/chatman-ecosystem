from .topology import FusionTopology

def bounded_standing(topology,blockers):
    if blockers: return "BLOCKED","DEPENDENCY_RED"
    if topology==FusionTopology.HEALTHY: return "PARTIAL_ALIVE","FUSION_CURRENT_BOUNDED"
    if topology in {FusionTopology.CORRELATED,FusionTopology.DIVERGENT,FusionTopology.UNDER_SUPPORTED,FusionTopology.STALE}:
        return "UNKNOWN",topology.value
    return "UNKNOWN","UNCLASSIFIED"
