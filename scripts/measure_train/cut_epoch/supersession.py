from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class CutSupersession:
    newer_cut_id:str
    older_cut_id:str
    newer_generation:int
    older_generation:int
    reason:str
    def __post_init__(self):
        if self.newer_cut_id==self.older_cut_id: raise Refused("REFUSED[SELF_SUPERSESSION]")
        if self.newer_generation <= self.older_generation: raise Refused("REFUSED[NON_FORWARD_CUT_SUPERSESSION]")
        if self.reason not in {"PRODUCER_ADVANCED","RECEIPT_SUPERSEDED","CORRECTION","DEPENDENCY_CHANGED"}: raise Refused("REFUSED[INVALID_CUT_SUPERSESSION_REASON]")
