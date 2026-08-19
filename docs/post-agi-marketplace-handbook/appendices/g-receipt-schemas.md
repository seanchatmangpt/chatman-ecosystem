# Appendix G — Receipt Schemas

Receipts bind consequence to identity and authority.

## Common envelope

```toml
schema = "chatman.marketplace.receipt.v1"
receipt_id = "..."
subject = "canonical-product-version-or-commercial-object"
marketplace = "..."
capability = "..."
actor = "..."
authority = "..."
intent_digest = "blake3:..."
observed_at = "..."
effective_at = "..."
external_ids = []
changed = []
verified = []
excluded = []
evidence_digests = []
replay = []
standing_before = "..."
standing_after = "..."
```

## Entitlement receipt

Add:

```text
agreement_id
entitlement_id
previous_state
new_state
source_event_id
idempotency_key
rights_delta
```

## Fulfillment receipt

Add:

```text
target_identity
deployment_artifact_digest
actuation_id
expected_postcondition
observed_postcondition
compensation_identity?
```

## Metering receipt

Add:

```text
meter_definition_version
window_start
window_end
usage_event_digest_set
quantity
unit
submission_external_id
vendor_acceptance_state
```

## Offer receipt

Add:

```text
offer_id
buyer_scope
plan_version
price_terms_digest
legal_terms_digest
valid_from
valid_until
vendor_offer_id
```

## Receipt DAG

A receipt should link prerequisite receipts by digest rather than copy mutable narratives. A sale can therefore be reconstructed as a DAG:

```text
product-admission
      ↓
offer → agreement → entitlement → fulfillment
                        ↓             ↓
                      usage → meter → settlement
                        ↓
                     support
```

A replay consumes this DAG but does not inherit DO authority from it.
