from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True)
class ConsistentCut:
    epochs: tuple
    def __post_init__(self):
        repos=[e.subject.repo for e in self.epochs]
        if len(repos) != len(set(repos)):
            raise Refused("REFUSED[DUPLICATE_CUT_REPOSITORY]")

    def by_repo(self):
        return {e.subject.repo:e for e in self.epochs}
