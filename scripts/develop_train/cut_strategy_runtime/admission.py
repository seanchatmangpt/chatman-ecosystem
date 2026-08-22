from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .cut import EvidenceCut
from .epoch import ProducerEpoch
from .identity import Refusal
@dataclass(frozen=True, slots=True)
class CutAdmission:
    cut: EvidenceCut
    current_epochs: tuple[ProducerEpoch, ...]
    now: datetime
    def admit(self) -> EvidenceCut:
        if not (self.cut.valid_from <= self.now < self.cut.valid_until):
            raise Refusal("REFUSED[EXPIRED_OR_NOT_YET_VALID_CUT]")
        current = {e.subject.repository: e for e in self.current_epochs}
        selected = self.cut.epoch_map()
        if set(selected) != set(current):
            raise Refusal("REFUSED[INCOMPLETE_CURRENT_PRODUCER_SET]")
        for repo, epoch in selected.items():
            live = current[repo]
            if (epoch.generation, epoch.receipt, epoch.subject.sha) != (live.generation, live.receipt, live.subject.sha):
                raise Refusal("REFUSED[STALE_CUT_EPOCH]")
        return self.cut
