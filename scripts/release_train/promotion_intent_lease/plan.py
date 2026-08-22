from dataclasses import dataclass
from .subject import Subject

@dataclass(frozen=True)
class PromotionPlan:
    subject_order: tuple[Subject,...]
    phases: tuple[str,...]=('VERIFY','CONSTRUCT')
    def __post_init__(self):
        if any(x not in {'VERIFY','CONSTRUCT'} for x in self.phases):
            raise ValueError('REFUSED[PLAN_CONTAINS_DO]')
