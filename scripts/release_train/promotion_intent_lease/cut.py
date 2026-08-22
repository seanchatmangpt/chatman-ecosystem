from dataclasses import dataclass
from .subject import Subject, Refusal

@dataclass(frozen=True)
class CutIdentity:
    cut_id: str
    generation: int
    producers: tuple[Subject, ...]

    def __post_init__(self):
        if self.generation < 0:
            raise Refusal('REFUSED[INVALID_CUT_GENERATION]')
        if not self.cut_id or len(set(self.producers)) != len(self.producers):
            raise Refusal('REFUSED[INVALID_CUT_IDENTITY]')
