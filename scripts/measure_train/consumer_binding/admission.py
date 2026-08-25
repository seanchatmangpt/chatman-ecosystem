from .subject import Refused
from .scope import scope_satisfies

def admit_claim(claim, current_producer, observed_scope, now):
    if now.tzinfo is None:
        raise Refused("REFUSED[NAIVE_NOW]")
    if claim.producer.subject != current_producer.subject:
        raise Refused("REFUSED[FOREIGN_PRODUCER_SUBJECT]")
    if claim.producer.receipt_sha256 != claim.lease.bound_receipt_sha256:
        raise Refused("REFUSED[CLAIM_LEASE_RECEIPT_MISMATCH]")
    if claim.producer.receipt_sha256 != current_producer.receipt_sha256:
        raise Refused("REFUSED[SUPERSEDED_PRODUCER_RECEIPT]")
    if claim.producer.schema != current_producer.schema:
        raise Refused("REFUSED[PRODUCER_SCHEMA_DRIFT]")
    if now < claim.lease.issued_at:
        raise Refused("REFUSED[LEASE_NOT_YET_VALID]")
    if now >= claim.lease.expires_at:
        raise Refused("REFUSED[EXPIRED_EVIDENCE_LEASE]")
    if not scope_satisfies(observed_scope, claim.required_scope):
        raise Refused("REFUSED[INSUFFICIENT_EVIDENCE_SCOPE]")
    return "ADMITTED"
