from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .persistence import StoreKind
from .strategy import CutStrategy
@dataclass(frozen=True, slots=True)
class QualificationReceipt:
    schema: str
    consumer: str
    selected_cut: str
    strategy: CutStrategy
    store: StoreKind
    standing: str
    frontier: tuple[str, ...]
    actuation_performed: bool
    digest: str
def issue_receipt(*, consumer: str, selected_cut: str, strategy: CutStrategy, store: StoreKind, standing: str, frontier: tuple[str, ...], actuation_performed: bool) -> QualificationReceipt:
    payload = {"schema":"chatman.develop-cut-strategy/1","consumer":consumer,"selected_cut":selected_cut,"strategy":strategy.value,"store":store.value,"standing":standing,"frontier":list(frontier),"actuation_performed":actuation_performed}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return QualificationReceipt(payload["schema"], consumer, selected_cut, strategy, store, standing, frontier, actuation_performed, digest)
def replay_receipt(receipt: QualificationReceipt) -> bool:
    rebuilt = issue_receipt(consumer=receipt.consumer, selected_cut=receipt.selected_cut, strategy=receipt.strategy, store=receipt.store, standing=receipt.standing, frontier=receipt.frontier, actuation_performed=receipt.actuation_performed)
    return rebuilt.digest == receipt.digest
