from dataclasses import dataclass
from .refusal import Refused
FAMILIES={"SEARCH","SEMANTIC","DISTRIBUTED","SIMULATION"}
@dataclass(frozen=True)
class ControlIdentity:
 family:str; implementation:str; model_digest:str; evidence_root:str
 def __post_init__(self):
  if self.family not in FAMILIES: raise Refused("REFUSED[UNKNOWN_CONTROL_FAMILY]")
  if not self.implementation or len(self.model_digest)!=64 or len(self.evidence_root)!=64: raise Refused("REFUSED[INVALID_CONTROL_IDENTITY]")
