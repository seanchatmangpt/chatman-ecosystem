from dataclasses import dataclass
from .calibration import Calibration
from .receipt import Receipt, manufacture
from .subject import Subject

@dataclass(frozen=True)
class Qualification:
    standing: str
    blockers: tuple[str,...]
    receipt: Receipt | None

def qualify(subject: Subject, calibration: Calibration, dependency_blockers: tuple[str,...],
            availability_lower: float, required_availability: float=0.5,
            max_false_current_rate: float=0.2) -> Qualification:
    if dependency_blockers:
        return Qualification("BUILD_BROKEN", dependency_blockers, None)
    if availability_lower < required_availability or calibration.false_current_rate > max_false_current_rate:
        return Qualification("UNSUPPORTED", (), None)
    standing="PARTIAL_ALIVE"
    return Qualification(standing, (), manufacture(subject, calibration.generation, standing, calibration.digest))
