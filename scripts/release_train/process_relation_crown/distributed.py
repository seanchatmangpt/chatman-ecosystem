from dataclasses import dataclass
from datetime import datetime,timezone
from .refusal import Refused
@dataclass(frozen=True)
class HostWitness:
    host:str; region:str; semantic_digest:str; trace_digest:str; encrypted:bool; cert_digest:str; observed_at:datetime
def require_current(rows,now:datetime,max_age_seconds:int=3600):
    if len({r.host for r in rows})<2 or len({r.region for r in rows})<2: raise Refused("INSUFFICIENT_DISTRIBUTED_INDEPENDENCE")
    if any(not r.encrypted or not r.cert_digest for r in rows): raise Refused("TLS_CORRESPONDENCE_FAILURE")
    if len({(r.semantic_digest,r.trace_digest) for r in rows})!=1: raise Refused("DISTRIBUTED_TRACE_DIVERGENCE")
    now=now.astimezone(timezone.utc)
    if any((now-r.observed_at.astimezone(timezone.utc)).total_seconds()>max_age_seconds for r in rows): raise Refused("STALE_DISTRIBUTED_WITNESS")
    return True
