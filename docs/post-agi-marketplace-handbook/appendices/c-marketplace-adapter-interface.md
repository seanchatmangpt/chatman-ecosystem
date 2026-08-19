# Appendix C — Marketplace Adapter Interface

The adapter interface preserves one canonical commercial protocol while allowing vendor wire contracts to differ.

```text
trait MarketplaceAdapter {
  describe_capabilities() -> CapabilityDescriptor

  parse_customer_resolution(input) -> Candidate<CustomerResolution>
  parse_commercial_event(input) -> Candidate<CommercialEvent>
  parse_entitlement_event(input) -> Candidate<EntitlementEvent>

  construct_offer_intent(Offer*) -> Intent
  construct_meter_intent(MeterBatch*) -> Intent
  construct_fulfillment_ack_intent(FulfillmentReceipt*) -> Intent

  observe_offer(external_id) -> Observation<OfferState>
  observe_entitlement(external_id) -> Observation<EntitlementState>
  observe_meter_submission(external_id) -> Observation<MeterState>
}
```

The interface deliberately does **not** expose an ambient `execute()` method.

## Adapter obligations

- Preserve vendor request/response payloads or hashes needed for evidence.
- Verify signatures, tokens, issuer identity, or authenticated channel provenance according to the vendor contract.
- Map vendor object IDs to canonical IDs without replacing them.
- Treat unknown enum/state values as `UNKNOWN` or typed refusal, never default success.
- Keep effective time distinct from arrival time.
- Construct deterministic idempotency identities.
- Expose capability/version metadata.
- Route external mutations through the BRCE broker.
- Return enough evidence to verify postconditions independently.

## Error taxonomy

```text
REFUSED:INVALID_SIGNATURE
REFUSED:ISSUER_MISMATCH
REFUSED:SUBJECT_UNRESOLVED
REFUSED:STALE_EVENT
REFUSED:UNKNOWN_PRODUCT_MAPPING
REFUSED:UNKNOWN_PLAN_MAPPING
REFUSED:ILLEGAL_STATE_TRANSITION
REFUSED:AUTHORITY_MISSING
REFUSED:IDEMPOTENCY_CONFLICT
UNSUPPORTED:VENDOR_CAPABILITY
BLOCKED:EXTERNAL_VENDOR_STATE
UNKNOWN:UNOBSERVED_RESULT
```

Vendor SDK exceptions should be preserved as diagnostic evidence but translated into canonical failure classes at the boundary.

## Versioning

An adapter version binds:

```text
canonical_ontology_digest
vendor_contract_version_or_observation_date
generator_version
pack_version
source_commit
tests_digest
```

Changing any identity invalidates reuse of prior ALIVE evidence unless equivalence is separately proven.
