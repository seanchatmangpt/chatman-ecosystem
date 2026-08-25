from dataclasses import dataclass
from .interval import Interval
from .subject import Subject
from .errors import Refused
_ALLOWED={'semantic','trace','calibration','selector','realization','methodology','runtime','security','authority','replay'}
@dataclass(frozen=True)
class EvidenceNode:
    evidence_id:str; subject:Subject; kind:str; generation:int; interval:Interval; implementation:str; model:str; domain:str; cost:float=0.0
    def __post_init__(self):
        if self.kind not in _ALLOWED: raise Refused('REFUSED[INVALID_EVIDENCE_KIND]')
        if self.generation < 0 or self.cost < 0: raise Refused('REFUSED[INVALID_EVIDENCE_VALUE]')
        if not self.evidence_id or not self.implementation or not self.model or not self.domain: raise Refused('REFUSED[EMPTY_EVIDENCE_IDENTITY]')
