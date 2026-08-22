from dataclasses import dataclass
from datetime import datetime

from .authority import ActionClass, admit_action
from .belief import Belief
from .budget import AcquisitionBudget
from .calibration import SensorCalibration
from .candidate import EvidenceCandidate
from .dependency import DependencyGraph
from .frontier import CalibrationFrontier
from .independence import IndependenceProof
from .receipt import QualificationReceipt
from .selector import select
from .standing import bounded_standing
from .strategy import Strategy
from .subject import Subject

@dataclass(frozen=True)
class Qualification:
    selected_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    standing: str
    phases: tuple[str, ...]
    receipt: QualificationReceipt

def qualify(
    subject_value: str,
    belief: Belief,
    candidates: tuple[EvidenceCandidate, ...],
    calibrations: tuple[SensorCalibration, ...],
    proofs: tuple[IndependenceProof, ...],
    budget: AcquisitionBudget,
    strategy: Strategy,
    frontier: CalibrationFrontier,
    dependencies: DependencyGraph,
    dependency_standing: dict[str, str],
    now: datetime,
) -> Qualification:
    subject = Subject.parse(subject_value)
    for calibration in calibrations:
        calibration.admit(now)
    frontier.assert_current(calibrations)
    blockers = dependencies.blockers(subject.repo, dependency_standing)
    selected: tuple[EvidenceCandidate, ...] = ()
    if not blockers:
        selected = select(belief, candidates, calibrations, proofs, budget, strategy)
    standing = bounded_standing(len(selected), blockers)
    admit_action(ActionClass.SELECT)
    admit_action(ActionClass.CONSTRUCT)
    receipt = QualificationReceipt.issue(
        subject.canonical(), frontier.digest, strategy.value, tuple(item.id for item in selected), standing
    )
    return Qualification(tuple(item.id for item in selected), blockers, standing, ("VERIFY", "CONSTRUCT"), receipt)
