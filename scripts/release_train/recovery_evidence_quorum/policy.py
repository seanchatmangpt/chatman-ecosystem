from dataclasses import dataclass
@dataclass(frozen=True)
class QuorumPolicy:
    min_independent_clusters:int=2
    required_scope:str="REPOSITORY"
    def __post_init__(self):
        if self.min_independent_clusters<1: raise ValueError("REFUSED[INVALID_QUORUM]")
def standing_for(clusters,policy,blockers):
    if blockers:return "BLOCKED"
    outcomes=[]; pass_clusters=0
    for cluster in clusters:
        values={w.outcome for w in cluster}; outcomes.extend(values)
        if "FAIL" in values:return "BUILD_BROKEN"
        if values=={"PASS"} and all(w.scope==policy.required_scope for w in cluster): pass_clusters+=1
    if pass_clusters>=policy.min_independent_clusters:return "PARTIAL_ALIVE"
    if outcomes and all(value=="UNSUPPORTED" for value in outcomes):return "UNSUPPORTED"
    return "UNKNOWN"
