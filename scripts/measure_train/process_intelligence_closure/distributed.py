from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class RegionWitness:
    subject: Subject
    region: str
    host: str
    semantic_digest: str
    observed_at: datetime
    def __post_init__(self):
        if not self.region or not self.host: raise Refused("REFUSED[EMPTY_REGION_IDENTITY]")
        if len(self.semantic_digest)!=64: raise Refused("REFUSED[INVALID_SEMANTIC_DIGEST]")

def distributed_currentness(subject,witnesses,now,max_age_seconds):
    rows=tuple(witnesses)
    if not rows: return {"state":"UNKNOWN","regions":0}
    for w in rows:
        if w.subject!=subject: raise Refused("REFUSED[FOREIGN_REGION_SUBJECT]")
        age=(now-w.observed_at).total_seconds()
        if age<0: raise Refused("REFUSED[FUTURE_REGION_EVIDENCE]")
        if age>max_age_seconds: return {"state":"STALE","regions":len({x.region for x in rows})}
    if len({w.semantic_digest for w in rows})>1: return {"state":"DIVERGED","regions":len({x.region for x in rows})}
    return {"state":"CURRENT","regions":len({x.region for x in rows})}
