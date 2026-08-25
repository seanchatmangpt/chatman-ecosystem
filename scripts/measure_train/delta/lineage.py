from dataclasses import dataclass
@dataclass(frozen=True)
class LineageObservation:
    predecessor_pr:int; state:str; merged:bool; base_sha:str; head_sha:str
    def admit(self):
        if self.state=="open" and not self.merged: return "ADMITTED_OPEN_HEAD"
        if self.merged: return "REQUIRE_CONTAINMENT_PROOF"
        raise ValueError("REFUSED[SCHEDULE_PR_LINEAGE]")
