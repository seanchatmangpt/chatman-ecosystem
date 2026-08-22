from dataclasses import dataclass
from . import DependencySubject, Refusal

@dataclass(frozen=True)
class PinTransition:
    current: DependencySubject
    candidate: DependencySubject
    ancestry: str

    def admit(self) -> DependencySubject:
        if self.current.repo != self.candidate.repo:
            raise Refusal('REFUSED[PIN_REPOSITORY_DRIFT]')
        if self.current.sha == self.candidate.sha:
            raise Refusal('REFUSED[UNCHANGED_PIN]')
        if self.ancestry != 'descendant':
            raise Refusal('REFUSED[UNPROVEN_PIN_ANCESTRY]')
        return self.candidate
