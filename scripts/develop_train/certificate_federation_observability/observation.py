from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from .transport import TransportState
from .errors import Refused
class Relation(str,Enum): EXACT="EXACT"; ADVANCED="ADVANCED"; DIVERGED="DIVERGED"; CENSORED="CENSORED"
@dataclass(frozen=True)
class Observation:
    observation_id:str; transport_id:str; certificate_generation:int; state:TransportState; relation:Relation; observed_sha:str|None; semantic_digest:str|None; certificate_digest:str|None; observed_at:datetime; latency_ms:float
    def __post_init__(self):
        if not self.observation_id or self.certificate_generation<0 or self.latency_ms<0: raise Refused("INVALID_OBSERVATION")
        if self.observed_at.tzinfo is None: raise Refused("NAIVE_TIME")
        if self.state==TransportState.RESOLVED:
            if self.relation==Relation.CENSORED or not (self.observed_sha and self.semantic_digest and self.certificate_digest): raise Refused("RESOLVED_EVIDENCE_INCOMPLETE")
        elif self.relation!=Relation.CENSORED or any((self.observed_sha,self.semantic_digest,self.certificate_digest)): raise Refused("CENSORED_EVIDENCE_SHAPE")
def admit(observations,generation):
    obs=tuple(observations)
    if not obs: raise Refused("EMPTY_OBSERVATIONS")
    ids=[o.observation_id for o in obs]
    if len(ids)!=len(set(ids)): raise Refused("DUPLICATE_OBSERVATION")
    now=datetime.now(timezone.utc)
    for o in obs:
        if o.certificate_generation!=generation: raise Refused("FOREIGN_GENERATION")
        if o.observed_at>now: raise Refused("FUTURE_OBSERVATION")
    return tuple(sorted(obs,key=lambda o:(o.observed_at,o.observation_id)))
