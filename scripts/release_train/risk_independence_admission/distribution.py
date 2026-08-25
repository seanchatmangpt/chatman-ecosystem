from dataclasses import dataclass
from datetime import datetime, timezone
from .errors import Refused
@dataclass(frozen=True)
class HostEvidence:
    host:str; region:str; tls:bool; certificate_digest:str; observed_at:datetime
def require_distribution(hosts,now,max_age_seconds):
    hs=tuple(hosts)
    if len({h.host for h in hs})<2: raise Refused('MULTI_HOST_EVIDENCE_REQUIRED')
    if len({h.region for h in hs})<2: raise Refused('MULTI_REGION_EVIDENCE_REQUIRED')
    for h in hs:
        if not h.tls or not h.certificate_digest: raise Refused('TLS_CORRESPONDENCE_REQUIRED')
        if h.observed_at.tzinfo is None: raise Refused('NAIVE_DISTRIBUTED_TIMESTAMP')
        age=(now.astimezone(timezone.utc)-h.observed_at.astimezone(timezone.utc)).total_seconds()
        if age<0: raise Refused('DISTRIBUTED_EVIDENCE_FROM_FUTURE')
        if age>max_age_seconds: raise Refused('STALE_DISTRIBUTED_EVIDENCE')
    return True
