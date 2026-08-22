from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
class StoreKind(str, Enum):
    MEMORY="MEMORY"; JSONL="JSONL"; SQLITE="SQLITE"
@dataclass(frozen=True, slots=True)
class PersistenceNeed:
    durable: bool=False
    transactional: bool=False
def candidates() -> tuple[StoreKind, ...]: return (StoreKind.MEMORY, StoreKind.JSONL, StoreKind.SQLITE)
def select_store(need: PersistenceNeed) -> StoreKind:
    if need.transactional: return StoreKind.SQLITE
    if need.durable: return StoreKind.JSONL
    return StoreKind.MEMORY
