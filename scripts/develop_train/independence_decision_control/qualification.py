from dataclasses import dataclass

from .authority import ActionClass, admit
from .failure import require_failures
from .methodologies import require_methodologies
from .standing import standing


@dataclass(frozen=True)
class Qualification:
    decision: str
    standing: str
    generation: int


def qualify(*, decision, generation, calibrated, drift, methodologies, failures, dependency="PARTIAL_ALIVE"):
    admit(ActionClass.SELECT)
    require_methodologies(methodologies)
    require_failures(failures)
    return Qualification(decision, standing(dependency=dependency, drift=drift, calibrated=calibrated, closure=True), generation)
