from dataclasses import dataclass
from .correspondence import admit as admit_corr
from .currentness import require_current
from .coverage import Coverage
from .failure import standing
from .receipt import Receipt
@dataclass(frozen=True)
class Qualification:
    standing:str; generation:int; receipt:Receipt|None
class TraceCorrespondenceEngine:
    def qualify(self,subject,evidence,currentness,coverage:Coverage,now,failures=()):
        corr=admit_corr(evidence); generation=require_current(currentness,now); s=standing(failures)
        if not coverage.complete: s="UNKNOWN"
        r=None if s=="UNKNOWN" else Receipt(subject.value,corr.semantic_digest,corr.trace_digest,generation,s,False)
        return Qualification(s,generation,r)
