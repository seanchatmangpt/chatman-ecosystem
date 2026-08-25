from dataclasses import dataclass
from .interval import Interval
from .provenance import Provenance
VALID_KINDS={"SEMANTIC","TRACE","CALIBRATION","SELECTOR","REALIZATION","METHODOLOGY","ENGINE","ORACLE","REGION","SECURITY","FAILURE","REPLAY"}
@dataclass(frozen=True)
class Evidence:
    evidence_id:str; generation:int; kind:str; interval:Interval; provenance:Provenance; digest:str; parents:tuple[str,...]=()
    def __post_init__(self):
        if self.generation < 0: raise ValueError("generation")
        if self.kind not in VALID_KINDS: raise ValueError("kind")
        if len(self.digest)!=64: raise ValueError("digest")
