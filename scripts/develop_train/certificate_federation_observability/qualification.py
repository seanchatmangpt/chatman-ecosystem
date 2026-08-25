from dataclasses import dataclass
import hashlib,json
from .observation import admit as admit_obs
from .censoring import summarize
from .availability import wilson
from .lineage import classify as lineage_classify, require_no_divergence
from .currentness import evaluate as current_evaluate, require_current
from .quorum import exact_quorum
from .receipt import Receipt
@dataclass(frozen=True)
class Qualification: standing:str; availability_lower:float; current:int; censored:int; receipt:Receipt|None
def qualify(subject,certificate,observations,dependency_standing=()):
    obs=admit_obs(observations,certificate.generation)
    if "BUILD_BROKEN" in dependency_standing: return Qualification("BUILD_BROKEN",0,0,0,None)
    if "BLOCKED" in dependency_standing: return Qualification("BLOCKED",0,0,0,None)
    require_no_divergence(lineage_classify(obs)); c=require_current(current_evaluate(obs),2); q=exact_quorum(obs,2); cs=summarize(obs); w=wilson(cs.resolved,cs.resolved+cs.censored)
    standing="PARTIAL_ALIVE" if w.lower>=0.2 else "UNKNOWN"
    payload={"subject":subject.key,"generation":certificate.generation,"certificate":certificate.digest,"transports":q.transports,"current":c.current}
    qd=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest(); r=Receipt(subject.key,certificate.generation,standing,qd)
    return Qualification(standing,w.lower,c.current,c.censored,r)
