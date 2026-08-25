from dataclasses import dataclass
import hashlib, json, re
from .identity import Subject
from .refusal import require

_HEX64=re.compile(r"^[0-9a-f]{64}$")

def canonical_digest(body) -> str:
    raw=json.dumps(body, sort_keys=True, separators=(",",":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()

@dataclass(frozen=True)
class ReceiptNode:
    kind: str
    subject: Subject
    parents: tuple[str, ...]
    payload_digest: str
    actuation_performed: bool

    def __post_init__(self):
        require(bool(self.kind), "EMPTY_RECEIPT_KIND")
        require(bool(_HEX64.fullmatch(self.payload_digest)), "INVALID_RECEIPT_PAYLOAD_DIGEST")
        require(all(_HEX64.fullmatch(p) for p in self.parents), "INVALID_RECEIPT_PARENT")

    @property
    def digest(self):
        return canonical_digest({"kind":self.kind,"subject":self.subject.canonical,"parents":sorted(self.parents),"payload_digest":self.payload_digest,"actuation_performed":self.actuation_performed})

def require_dag(nodes):
    by={n.digest:n for n in nodes}
    require(len(by)==len(nodes), "DUPLICATE_RECEIPT_NODE")
    def visit(d,stack,done):
        if d in stack: require(False,"RECEIPT_CYCLE")
        if d in done: return
        stack.add(d)
        for p in by[d].parents:
            require(p in by, "FOREIGN_RECEIPT_PARENT")
            visit(p,stack,done)
        stack.remove(d); done.add(d)
    done=set()
    for d in by: visit(d,set(),done)
    return tuple(sorted(by))
