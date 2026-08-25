from dataclasses import dataclass
from datetime import datetime
from .subject import Subject,Refused
from .vector_clock import VectorClock
@dataclass(frozen=True, order=True)
class ReplicaObservation:
    subject: Subject; replica_id:str; generation:int; value_digest:str; clock:VectorClock; observed_at:datetime; receipt_sha256:str
    def __post_init__(self):
        if not self.replica_id.strip(): raise Refused("REFUSED[EMPTY_REPLICA_ID]")
        if self.generation<0: raise Refused("REFUSED[INVALID_GENERATION]")
        for value,name in ((self.value_digest,"VALUE"),(self.receipt_sha256,"RECEIPT")):
            if len(value)!=64 or any(c not in "0123456789abcdef" for c in value): raise Refused(f"REFUSED[INVALID_{name}_DIGEST]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_OBSERVATION_TIME]")
