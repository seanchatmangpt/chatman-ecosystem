from dataclasses import dataclass
import re
SHA=re.compile(r"^[0-9a-f]{40}$")
@dataclass(frozen=True)
class HeadDelta:
    repo:str; before:str; after:str
    def __post_init__(self):
        if "/" not in self.repo or not SHA.fullmatch(self.before) or not SHA.fullmatch(self.after):
            raise ValueError("REFUSED[INVALID_EXACT_SUBJECT_DELTA]")
    @property
    def moved(self): return self.before != self.after
