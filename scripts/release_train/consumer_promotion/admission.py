from dataclasses import dataclass
from datetime import datetime
from .claim import ConsumptionClaim
from .evidence import ProducerEvidence
from .scope import covers
@dataclass(frozen=True)
class Admission:
    admitted:bool
    reason:str
def admit(claim:ConsumptionClaim, evidence:ProducerEvidence, current_receipt:str, current_schema:str, now:datetime)->Admission:
    if claim.producer != evidence.subject: return Admission(False,"REFUSED[FOREIGN_PRODUCER]")
    if claim.receipt != evidence.receipt: return Admission(False,"REFUSED[CLAIM_RECEIPT_MISMATCH]")
    if claim.receipt != current_receipt: return Admission(False,"REFUSED[SUPERSEDED_RECEIPT]")
    if claim.schema != evidence.schema or claim.schema != current_schema: return Admission(False,"REFUSED[SCHEMA_DRIFT]")
    if not claim.lease.active(now): return Admission(False,"REFUSED[LEASE_INACTIVE]")
    if not covers(evidence.scope, claim.required_scope): return Admission(False,"REFUSED[SCOPE_LAUNDERING]")
    if evidence.standing in {"BUILD_BROKEN","BLOCKED"}: return Admission(False,f"BLOCKED[PRODUCER_{evidence.standing}]")
    if evidence.standing in {"UNKNOWN","UNSUPPORTED"}: return Admission(False,f"BLOCKED[PRODUCER_{evidence.standing}]")
    return Admission(True,"ADMITTED")
