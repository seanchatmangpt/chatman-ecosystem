from dataclasses import dataclass
CANDIDATES=("MEMORY","JSONL","SQLITE")
@dataclass(frozen=True)
class PersistenceNeed:
    durable: bool=False; transactional: bool=False

def select_store(need):
    if need.transactional: return "SQLITE"
    if need.durable: return "JSONL"
    return "MEMORY"
