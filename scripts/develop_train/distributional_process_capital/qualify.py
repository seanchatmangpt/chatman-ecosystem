from dataclasses import dataclass
from fractions import Fraction
import hashlib,json
from .methodology import require_methods
from .failures import require_complete
from .correspondence import require_engines,require_regions
from .receipt import Receipt
HARD={"BUILD_BROKEN","BLOCKED"}
@dataclass(frozen=True)
class Qualification:
    standing:str
    worst_risk:Fraction
    receipt:Receipt|None

def qualify(subject,strategy,calibration,candidate,methods,engines,regions,worlds,dependencies=()):
    hard=next((d for d in dependencies if d in HARD),None)
    if hard:
        return Qualification(hard,candidate.worst,None)
    if not calibration.admitted():
        return Qualification("UNSUPPORTED",candidate.worst,None)
    require_methods(methods)
    require_engines(engines)
    require_regions(regions)
    require_complete(worlds)
    standing="PARTIAL_ALIVE" if candidate.worst<=Fraction(1,2) else "UNSUPPORTED"
    payload={"subject":subject.key,"strategy":strategy.value,"calibration":calibration.digest,"candidate":candidate.name,"worst":str(candidate.worst)}
    evidence=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    receipt=Receipt(subject.key,strategy.value,standing,evidence) if standing=="PARTIAL_ALIVE" else None
    return Qualification(standing,candidate.worst,receipt)
