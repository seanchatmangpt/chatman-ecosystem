from dataclasses import dataclass
from datetime import datetime,timedelta
from .refusal import Refused
@dataclass(frozen=True)
class HostObservation:
    host:str; region:str; generation:int; encrypted:bool; certificate_digest:str; observed_at:datetime

def require_distributed(items, generation:int, now:datetime, max_age=timedelta(hours=1)):
    if len(items)<2 or len({x.host for x in items})<2 or len({x.region for x in items})<2: raise Refused("INSUFFICIENT_MULTI_REGION_TOPOLOGY")
    for x in items:
        if x.generation!=generation: raise Refused("STALE_DISTRIBUTED_GENERATION")
        if not x.encrypted or not x.certificate_digest: raise Refused("TLS_SECURITY_CORRESPONDENCE_FAILED")
        if x.observed_at.tzinfo is None or x.observed_at>now or now-x.observed_at>max_age: raise Refused("STALE_DISTRIBUTED_OBSERVATION")
    return True
