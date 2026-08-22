from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .admission import CutAdmission
from .authority import ActionClass, require_nonconsequential
from .cut import EvidenceCut
from .epoch import ProducerEpoch
from .frontier import CutFrontier
from .identity import Subject
from .persistence import PersistenceNeed, select_store
from .receipt import QualificationReceipt, issue_receipt
from .strategy import CutStrategy, select_cut
@dataclass(frozen=True, slots=True)
class Qualification:
    selected_cut: EvidenceCut
    standing: str
    receipt: QualificationReceipt
def qualify(*, consumer: Subject, candidate_cuts: tuple[EvidenceCut, ...], current_epochs: tuple[ProducerEpoch, ...], now: datetime, strategy: CutStrategy, persistence: PersistenceNeed, action: ActionClass = ActionClass.CONSTRUCT) -> Qualification:
    require_nonconsequential(action)
    frontier = CutFrontier(candidate_cuts).current()
    admitted = tuple(CutAdmission(cut=c, current_epochs=current_epochs, now=now).admit() for c in frontier)
    selected = select_cut(admitted, strategy); store = select_store(persistence); standing = "PARTIAL_ALIVE"
    receipt = issue_receipt(consumer=consumer.coordinate, selected_cut=selected.cut_id, strategy=strategy, store=store, standing=standing, frontier=tuple(c.cut_id for c in admitted), actuation_performed=False)
    return Qualification(selected, standing, receipt)
