# 46. Generating Commercial Control Plane Adapters

## Generate structure, fence consequence

Marketplace APIs contain a large amount of structural repetition: request/response models, identifiers, enum mappings, endpoint clients, signatures, webhook parsers, pagination, retry metadata, and conversion code. These are excellent generation targets.

What generation must not do is smuggle external authority into the generated component.

```text
GeneratedAdapter : VendorObservation → CanonicalIntent
DO ∉ GeneratedAdapter.ambient_authority
```

## Generated inbound adapter

A generated webhook/event adapter can provide:

- exact vendor schema types;
- parser and validation code;
- signature/authenticated-channel verification hooks;
- source-event identity extraction;
- vendor-to-canonical mapping lookup;
- canonical candidate event construction;
- typed unknown/unsupported values;
- fixtures for every known event state.

It should return an intent/event to admission, not call fulfillment itself.

## Generated outbound adapter

Meter, offer, activation, and publication clients can generate a deterministic vendor request from an admitted canonical intent. The call site passes that request to the authority broker.

```text
MeterBatch*
  → construct VendorMeterRequest
  → validate
  → BRCE(authority)
  → vendor API
  → observe result
  → receipt
```

This architecture makes it possible to test generated code extensively without possessing production credentials.

## Unknown enum law

Vendor APIs evolve. Generated enum mappings should have an explicit unknown state and fail closed where the value changes rights or money.

```text
KnownVendorState → CanonicalState
UnknownVendorState → UNKNOWN / REFUSED
```

Never map unknown to the nearest known success state.

## Error taxonomy

Preserve raw vendor error identity for diagnosis while normalizing operational meaning:

```text
transport failure
unauthenticated/unauthorized
rate limited
invalid request
state conflict
idempotency conflict
vendor unavailable
ambiguous result
unsupported capability
```

Retry policy belongs to the canonical operation semantics, not a generic SDK retry loop.

## Source correspondence

Generated adapters bind the vendor contract/source observation used to manufacture them. When a vendor API or documentation changes, source drift invalidates prior generator correspondence and triggers requalification.

## Refusals

- `REFUSED:GENERATED_DIRECT_SIDE_EFFECT`
- `REFUSED:UNKNOWN_VENDOR_STATE_AS_SUCCESS`
- `REFUSED:SDK_AUTO_RETRY_ON_AMBIGUOUS_FINANCIAL_DO`
- `REFUSED:UNMAPPED_VENDOR_IDENTIFIER`
- `REFUSED:STALE_VENDOR_CONTRACT_SOURCE`

## Operational exercise

Specify generated surfaces for an entitlement webhook adapter and a metering client. Show the exact line of architecture where generated construction ends and brokered DO begins. Test that no generated method can change an external marketplace without a separate exact authority object.
