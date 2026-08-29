from dataclasses import dataclass
from .observation import admit
from .trajectory import Trajectory
from .potential import descent_fraction
from .oscillation import recurrent
from .dwell import require_dwell
from .calibration import calibrate,current
from .evidence_capital import capital,require_capital
from .methodology import require_methodologies
from .correspondence import require_correspondence
from .blockers import blockers
from .receipt import Receipt
@dataclass(frozen=True)
class Qualification:
    standing: str
    descent_fraction: float
    dwell: int
    false_fixed_rate: float
    effective_capital: float
    receipt: Receipt|None
def qualify(subject,observations,dependency_graph=None,dependency_standings=None):
    obs=admit(observations)
    hard=blockers(dependency_graph or {},dependency_standings or {})
    if hard: return Qualification("BUILD_BROKEN",0.0,0,1.0,0.0,None)
    trajectory=Trajectory.build(obs)
    require_methodologies(obs); require_correspondence(obs)
    cap=require_capital(capital(obs)); cal=current([calibrate(obs,trajectory.head.generation)])
    d=require_dwell(trajectory,2); descent=descent_fraction(trajectory)
    standing="PARTIAL_ALIVE"
    if recurrent(trajectory) or not cal.admitted or descent < 0.5: standing="UNKNOWN"
    receipt=Receipt(subject.key,trajectory.head.generation,standing,cal.digest)
    return Qualification(standing,descent,d,cal.false_fixed_rate,cap.effective,receipt)
