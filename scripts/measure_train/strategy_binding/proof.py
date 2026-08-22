from dataclasses import dataclass
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class SelectionProof:
    consumer:Subject
    selected_cut_id:str
    strategy_digest:str
    frontier_digest:str
    proof_id:str
    def __post_init__(self):
        if len(self.strategy_digest)!=64 or len(self.frontier_digest)!=64: raise Refused("REFUSED[INVALID_SELECTION_DIGEST]")
        if not self.selected_cut_id.strip() or not self.proof_id.strip(): raise Refused("REFUSED[INVALID_SELECTION_PROOF]")
