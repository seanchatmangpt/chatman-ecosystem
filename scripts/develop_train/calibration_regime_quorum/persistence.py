from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PersistenceNeed:
    durable:bool=False; transactional:bool=False
@dataclass(frozen=True,slots=True)
class PersistenceChoice:
    selected:str; candidates:tuple[str,...]=("MEMORY","JSONL","SQLITE")
def select_store(need:PersistenceNeed)->PersistenceChoice:
    if need.transactional: return PersistenceChoice("SQLITE")
    if need.durable: return PersistenceChoice("JSONL")
    return PersistenceChoice("MEMORY")
