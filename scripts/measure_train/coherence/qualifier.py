from dataclasses import dataclass
from .admission import admit
from .coverage import cover
from .coherence import evaluate
from .freshness import require_fresh
from .projection import to_ocel
from .receipt import manufacture

@dataclass(frozen=True)
class Qualification:
    standing: str
    receipt: dict
    telemetry: tuple
    actuation_performed: bool=False

def qualify(subject, obligations, witnesses, now, max_age, parent=None):
    admitted=admit(subject,obligations,witnesses)
    fresh=require_fresh(list(admitted),now,max_age)
    coverage=cover(obligations,list(fresh))
    coherence=evaluate(coverage)
    receipt=manufacture(subject,coherence,coverage,parent)
    return Qualification(coherence.standing.value,receipt,to_ocel(subject,fresh,coverage),False)
