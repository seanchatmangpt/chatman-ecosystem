from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .evidence import Evidence

def canonical(value)->bytes: return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

def evidence_doc(e: Evidence)->dict:
    return {'source_id':e.source_id,'subject':e.subject.identity,'kind':str(e.kind),'observed_at':e.observed_at.isoformat(),'outcome':str(e.outcome),'digest':e.digest,'detail':e.detail}

@dataclass(frozen=True)
class Receipt:
    schema: str
    subject: str
    observation_digest: str
    parent_digests: tuple[str,...]
    actuation_performed: bool=False

def manufacture(subject: str, rows: tuple[Evidence,...], parent_digests: tuple[str,...]=())->Receipt:
    body={'schema':'chatman.measure-train/1','subject':subject,'observations':[evidence_doc(e) for e in rows],'parents':sorted(parent_digests),'actuation_performed':False}
    return Receipt(body['schema'],subject,hashlib.sha256(canonical(body)).hexdigest(),tuple(sorted(parent_digests)),False)
