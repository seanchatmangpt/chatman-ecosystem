from dataclasses import dataclass
from .authority import ActionClass, admit_action
from .calibration import Calibration, current_calibration, cusum
from .correspondence import EngineEvidence, OracleEvidence, RegionEvidence, admit_correspondence
from .dependency import blockers
from .failure import admit_failure_worlds
from .methodology import admit_methodologies
from .pareto import Candidate, select
from .receipt import Receipt
from .strata import Stratum, worst_stratum
from .subject import Subject
from .refusal import require

@dataclass(frozen=True)
class Qualification:
    subject: Subject
    generation: int
    standing: str
    strategy: str
    blocker_ids: tuple[str,...]
    receipt: Receipt | None


def qualify(*,subject:Subject,generation:int,calibrations:tuple[Calibration,...],miss_limit:float,drift_values:tuple[float,...],strata:tuple[Stratum,...],methods:set[str],engines:tuple[EngineEvidence,...],oracles:tuple[OracleEvidence,...],regions:tuple[RegionEvidence,...],failure_worlds:dict[str,bool],dependency_graph:dict[str,tuple[str,...]],dependency_standing:dict[str,str],dependency_root:str,candidates:tuple[Candidate,...],strategy:str,evidence_digest:str) -> Qualification:
    current_calibration(calibrations,generation,miss_limit)
    require(not cusum(drift_values,miss_limit,0.0,0.15),'CALIBRATION_DRIFT')
    worst_stratum(strata,1,miss_limit)
    admit_methodologies(methods)
    admit_correspondence(engines,oracles,regions,generation)
    admit_failure_worlds(failure_worlds)
    blocked=blockers(dependency_graph,dependency_standing,dependency_root)
    if blocked:
        return Qualification(subject,generation,'BUILD_BROKEN',strategy,blocked,None)
    chosen=select(candidates,strategy)
    require(chosen.worst_risk<=miss_limit,'STRESS_RISK_EXCEEDED')
    admit_action(ActionClass.SELECT)
    standing='PARTIAL_ALIVE'
    receipt=Receipt('chatman.transport-invariance-crown/1',subject.identity,generation,standing,evidence_digest,strategy).seal()
    return Qualification(subject,generation,standing,strategy,(),receipt)
