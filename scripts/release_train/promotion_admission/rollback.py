from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject

class RollbackRefusal(ValueError):
    pass

@dataclass(frozen=True)
class RollbackBoundary:
    predecessor_sha: str
    staged_subjects: tuple[Subject, ...]
    external_compensation_required: bool=False

    def __post_init__(self) -> None:
        if len(self.predecessor_sha) != 40:
            raise RollbackRefusal("REFUSED[INEXACT_ROLLBACK_PREDECESSOR]")
        if self.external_compensation_required:
            raise RollbackRefusal("REFUSED[EXTERNAL_COMPENSATION_REQUIRED]")
