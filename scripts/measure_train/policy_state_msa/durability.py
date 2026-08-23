from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class RestartWitness:
    subject_sha:str; before_revision:int; after_revision:int; before_digest:str; after_digest:str; clean_shutdown:bool; recovered:bool
    def __post_init__(self):
        if self.after_revision < self.before_revision: raise Refused("REFUSED[RESTART_REVISION_REGRESSION]")
def durability_state(witness):
    if not witness.recovered: return "FAIL"
    if witness.after_revision != witness.before_revision or witness.after_digest != witness.before_digest: return "FAIL"
    return "PASS"
