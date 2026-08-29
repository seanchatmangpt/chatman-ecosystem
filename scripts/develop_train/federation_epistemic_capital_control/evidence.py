from dataclasses import dataclass
from datetime import datetime,timezone
from .errors import Refused
@dataclass(frozen=True)
class TransportEvidence:
    evidence_id:str; generation:int; transport_id:str; implementation:str; model:str; domain:str; common_cause:str; failure:bool; predicted_current:bool; realized_current:bool; information_gain:float; cost:float; methodology:str; engine:str; region:str; evidence_root:str; observed_at:datetime
    def __post_init__(self):
        if not self.evidence_id or self.generation<0: raise Refused("INVALID_EVIDENCE_IDENTITY")
        if any(not x for x in (self.transport_id,self.implementation,self.model,self.domain,self.common_cause,self.methodology,self.engine,self.region,self.evidence_root)): raise Refused("INCOMPLETE_EVIDENCE_PROVENANCE")
        if self.information_gain<0 or self.cost<0: raise Refused("NEGATIVE_INFORMATION_OR_COST")
        if self.observed_at.tzinfo is None: raise Refused("NAIVE_EVIDENCE_TIME")
def admit(xs,generation):
    xs=tuple(xs)
    if not xs: raise Refused("EMPTY_EPISTEMIC_CORPUS")
    ids=[x.evidence_id for x in xs]
    if len(ids)!=len(set(ids)): raise Refused("DUPLICATE_EVIDENCE")
    now=datetime.now(timezone.utc)
    for x in xs:
        if x.generation!=generation: raise Refused("FOREIGN_GENERATION")
        if x.observed_at>now: raise Refused("FUTURE_EVIDENCE")
    return tuple(sorted(xs,key=lambda x:(x.observed_at,x.evidence_id)))
