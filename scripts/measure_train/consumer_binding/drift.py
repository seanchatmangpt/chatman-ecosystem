def classify_drift(claim, current_producer, now):
    if claim.producer.subject != current_producer.subject:
        return "FOREIGN_SUBJECT"
    if claim.producer.receipt_sha256 != current_producer.receipt_sha256:
        return "SUPERSEDED_RECEIPT"
    if claim.producer.schema != current_producer.schema:
        return "SCHEMA_DRIFT"
    if now >= claim.lease.expires_at:
        return "LEASE_EXPIRED"
    if now < claim.lease.issued_at:
        return "LEASE_NOT_YET_VALID"
    return "CURRENT"
