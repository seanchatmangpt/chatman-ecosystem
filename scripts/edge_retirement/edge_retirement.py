"""Machine-check recurring-intelligence retirement without granting DO authority."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, re

EXACT = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_OWNERS = {"human", "llm"}

@dataclass(frozen=True)
class Edge:
    edge_id: str
    exact_subject: str
    owners: tuple[str, ...]
    consequence: str
    authority: str = "NONE"

@dataclass(frozen=True)
class Receipt:
    edge_id: str
    exact_subject: str
    consequence: str
    owners: tuple[str, ...]
    authority: str
    digest: str

def _canonical(edge: Edge) -> dict:
    owners = tuple(sorted(set(edge.owners)))
    if not edge.edge_id: raise ValueError("REFUSED:MISSING_EDGE_ID")
    if not EXACT.fullmatch(edge.exact_subject): raise ValueError("REFUSED:MUTABLE_SUBJECT")
    if not edge.consequence.strip(): raise ValueError("REFUSED:MISSING_CONSEQUENCE")
    if edge.authority != "NONE": raise ValueError("REFUSED:AUTHORITY_WIDENING")
    if not owners or "machine" not in owners: raise ValueError("REFUSED:NO_MACHINE_OWNER")
    if FORBIDDEN_OWNERS.intersection(owners): raise ValueError("REFUSED:RECURRING_INTELLIGENCE_REMAINS")
    if set(owners) != {"machine"}: raise ValueError("REFUSED:UNKNOWN_OWNER")
    return {"edge_id":edge.edge_id,"exact_subject":edge.exact_subject,
            "owners":owners,"consequence":edge.consequence.strip(),"authority":"NONE"}

def admit(edge: Edge) -> Receipt:
    p=_canonical(edge)
    raw=json.dumps(p,sort_keys=True,separators=(",",":")).encode()
    digest="sha256:"+hashlib.sha256(raw).hexdigest()
    return Receipt(p["edge_id"],p["exact_subject"],p["consequence"],p["owners"],"NONE",digest)

def replay(edge: Edge, receipt: Receipt) -> bool:
    return admit(edge) == receipt
