from __future__ import annotations
from dataclasses import dataclass
from .frontier import CandidateFrontier, CutCandidate
from .policy import StrategyPolicy, CutStrategy
from .intent import SelectionIntent
def select(frontier:CandidateFrontier,policy:StrategyPolicy)->CutCandidate:
    cs=frontier.candidates
    if policy.strategy is CutStrategy.LATEST_COMPLETE: return max(cs,key=lambda c:(c.generation,c.freshness,c.cut_id))
    if policy.strategy is CutStrategy.MAX_FRESHNESS: return max(cs,key=lambda c:(c.freshness,c.generation,c.cut_id))
    if policy.strategy is CutStrategy.MIN_SKEW: return min(cs,key=lambda c:(c.skew,-c.freshness,-c.generation,c.cut_id))
    raise ValueError("REFUSED[UNKNOWN_SELECTION_STRATEGY]")
@dataclass(frozen=True, slots=True)
class SelectionProof:
    intent:SelectionIntent
    def admit(self,frontier:CandidateFrontier,policy:StrategyPolicy)->CutCandidate:
        if self.intent.policy_digest!=policy.digest: raise ValueError("REFUSED[STALE_SELECTION_POLICY]")
        if self.intent.frontier_digest!=frontier.digest: raise ValueError("REFUSED[STALE_CANDIDATE_FRONTIER]")
        chosen=select(frontier,policy)
        if chosen.cut_id!=self.intent.selected_cut_id: raise ValueError("REFUSED[NON_REPRODUCIBLE_SELECTION]")
        return chosen
