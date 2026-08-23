from .quorum import QuorumResult
def bounded_standing(quorum:QuorumResult, blockers:tuple[str,...], causal_concurrent:bool)->tuple[str,str]:
    if blockers: return "BLOCKED","DEPENDENCY_BLOCKER"
    if quorum.policy_digest is None: return "UNKNOWN","NO_REPLICA_QUORUM"
    if quorum.split_brain or causal_concurrent: return "UNKNOWN","AMBIGUOUS_REPLICA_TOPOLOGY"
    return "PARTIAL_ALIVE","REPLICATED_POLICY_CURRENT"
