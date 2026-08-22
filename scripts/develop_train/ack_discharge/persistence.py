from dataclasses import dataclass
from enum import StrEnum
class StoreKind(StrEnum): MEMORY='MEMORY'; JSONL='JSONL'; SQLITE='SQLITE'
@dataclass(frozen=True,slots=True)
class StoreRequirements: durable:bool=False; transactional:bool=False
def candidates():return (StoreKind.MEMORY,StoreKind.JSONL,StoreKind.SQLITE)
def select(req):
 if req.transactional:return StoreKind.SQLITE
 if req.durable:return StoreKind.JSONL
 return StoreKind.MEMORY
