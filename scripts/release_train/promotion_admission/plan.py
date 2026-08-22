from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject

_ALLOWED={"VERIFY","CONSTRUCT"}

class PlanRefusal(ValueError):
    pass

@dataclass(frozen=True)
class PlanStep:
    phase: str
    subject: Subject
    action: str

    def __post_init__(self) -> None:
        if self.phase not in _ALLOWED:
            raise PlanRefusal("REFUSED[CONSEQUENTIAL_PLAN_PHASE]")

def build_plan(order: tuple[Subject, ...]) -> tuple[PlanStep, ...]:
    steps=[]
    for subject in order:
        steps.append(PlanStep("VERIFY", subject, "requalify_exact_subject"))
        steps.append(PlanStep("CONSTRUCT", subject, "stage_promotion_candidate"))
    return tuple(steps)
