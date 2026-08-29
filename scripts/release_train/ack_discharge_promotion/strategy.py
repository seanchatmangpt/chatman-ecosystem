from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject

class StrategyRefusal(ValueError):
    pass

@dataclass(frozen=True)
class Strategy:
    kind: str
    quorum: int | None = None
    critical: tuple[Subject,...] = ()

    def __post_init__(self) -> None:
        if self.kind not in {"ALL","QUORUM","CRITICAL_PATH"}:
            raise StrategyRefusal("REFUSED[UNKNOWN_DISCHARGE_STRATEGY]")
        if self.kind == "QUORUM":
            if self.quorum is None or self.quorum <= 0:
                raise StrategyRefusal("REFUSED[INVALID_QUORUM]")
        elif self.quorum is not None:
            raise StrategyRefusal("REFUSED[UNEXPECTED_QUORUM]")
        if self.kind == "CRITICAL_PATH" and not self.critical:
            raise StrategyRefusal("REFUSED[EMPTY_CRITICAL_PATH]")

    def complete(self, discharged: set[Subject], affected: tuple[Subject,...]) -> bool:
        if self.kind == "ALL":
            return set(affected) <= discharged
        if self.kind == "QUORUM":
            assert self.quorum is not None
            return len(discharged.intersection(affected)) >= self.quorum
        return set(self.critical) <= discharged
