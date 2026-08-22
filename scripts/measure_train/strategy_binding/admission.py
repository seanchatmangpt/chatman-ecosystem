from .subject import Refused
from .selection import select

def admit(proof, policy, candidates, frontier_digest):
    if proof.strategy_digest != policy.digest: raise Refused("REFUSED[STALE_SELECTION_POLICY]")
    if proof.frontier_digest != frontier_digest: raise Refused("REFUSED[STALE_CANDIDATE_FRONTIER]")
    selected=select(policy,candidates)
    if proof.selected_cut_id != selected.cut_id: raise Refused("REFUSED[NON_REPRODUCIBLE_SELECTION]")
    return selected
