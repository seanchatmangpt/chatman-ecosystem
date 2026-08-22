from dataclasses import dataclass
@dataclass(frozen=True)
class RollbackPlan:
    predecessor_sha:str
    candidate_sha:str
    replay_command:str
    external_compensation_required:bool=False
    def __post_init__(self):
        if self.external_compensation_required: raise ValueError("REFUSED[EXTERNAL_COMPENSATION_REQUIRED]")
        if self.predecessor_sha == self.candidate_sha: raise ValueError("REFUSED[NO_ROLLBACK_BOUNDARY]")
