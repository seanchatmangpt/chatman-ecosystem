from __future__ import annotations

from dataclasses import dataclass

from .admission import SubjectAdmission
from .authority import AuthorityContext
from .model import Refused


@dataclass(frozen=True)
class PlanStep:
    subject: str
    action: str
    reversible: bool


def build_plan(admissions: list[SubjectAdmission], authority: AuthorityContext) -> tuple[PlanStep, ...]:
    if not admissions:
        raise Refused("EMPTY_PROMOTION_PLAN")
    steps: list[PlanStep] = []
    for admission in admissions:
        authority.admit("VERIFY")
        steps.append(PlanStep(admission.subject.coordinate, "VERIFY", True))
        if admission.standing == "ALIVE":
            authority.admit("CONSTRUCT")
            steps.append(PlanStep(admission.subject.coordinate, "CONSTRUCT", True))
    if not any(step.action == "CONSTRUCT" for step in steps):
        raise Refused("NO_CONSTRUCTIBLE_SUBJECT")
    return tuple(steps)
