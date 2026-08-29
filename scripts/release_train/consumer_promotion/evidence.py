from dataclasses import dataclass
import re
from .subject import Subject
_HEX64=re.compile(r"^[0-9a-f]{64}$")
STANDINGS={"UNKNOWN","PARTIAL_ALIVE","ALIVE","BLOCKED","BUILD_BROKEN","UNSUPPORTED"}
@dataclass(frozen=True)
class ProducerEvidence:
    subject:Subject
    receipt:str
    schema:str
    standing:str
    scope:str
    def __post_init__(self):
        if not _HEX64.fullmatch(self.receipt): raise ValueError("REFUSED[INVALID_RECEIPT]")
        if not self.schema: raise ValueError("REFUSED[INVALID_SCHEMA]")
        if self.standing not in STANDINGS: raise ValueError("REFUSED[INVALID_STANDING]")
        if self.scope not in {"FOCUSED","INTEGRATION","REPOSITORY"}: raise ValueError("REFUSED[INVALID_SCOPE]")
