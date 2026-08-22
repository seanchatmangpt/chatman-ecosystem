from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
class StoreKind(str,Enum): MEMORY="MEMORY"; JSONL="JSONL"; SQLITE="SQLITE"
@dataclass(frozen=True,slots=True)
class PersistenceNeed: durable:bool=False; transactional:bool=False
@dataclass(frozen=True,slots=True)
class StoreCandidate: kind:StoreKind; durable:bool; transactional:bool
CANDIDATES=(StoreCandidate(StoreKind.MEMORY,False,False),StoreCandidate(StoreKind.JSONL,True,False),StoreCandidate(StoreKind.SQLITE,True,True))
def select_store(need:PersistenceNeed)->StoreCandidate:
    viable=[c for c in CANDIDATES if (not need.durable or c.durable) and (not need.transactional or c.transactional)]
    return viable[0]
