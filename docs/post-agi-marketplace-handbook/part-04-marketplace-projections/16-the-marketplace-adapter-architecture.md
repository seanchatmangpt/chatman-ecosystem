# 16. The Marketplace Adapter Architecture

## Adapter, projection, or fork?

A marketplace adapter is a semantic boundary between a vendor protocol and the canonical commercial graph. It is not a second business core.

```text
Vendor protocol
  ↕
Marketplace adapter
  ↕
Canonical commercial protocol
```

If AWS, Microsoft, Google, Oracle, SAP, or Salesforce adapters each contain their own plan-state, customer model, metering aggregation, and support logic, the product has already forked.

## Inbound side

An inbound adapter may handle purchase redirects, webhooks, queue messages, entitlement notifications, partner callbacks, package-license events, or data-share requests. Its responsibilities are bounded:

1. parse without consequence;
2. verify authenticated-channel provenance, signature, token, or issuer according to the vendor contract;
3. preserve the raw observation or digest;
4. resolve vendor identifiers to canonical subjects;
5. translate into a typed candidate event;
6. invoke commercial admission;
7. emit an admitted canonical event or typed failure.

It does **not** directly grant rights because a payload passed schema validation.

## Outbound side

An outbound adapter constructs vendor-specific requests for offers, activation acknowledgments, meter batches, package publication, or other marketplace operations.

Construction remains reversible:

```text
CanonicalIntent
  → vendor request candidate
  → validate
  → authority envelope
  → BRCE DO
  → observe vendor postcondition
  → receipt
```

The generated request must not contain a hidden `execute` path that bypasses the broker.

## Capability descriptors

Every adapter should expose the semantics it actually supports:

```text
marketplace
adapter_version
vendor_contract_observed_at
supported_product_types
supported_offer_classes
entitlement_model
metering_model
fulfillment_models
private_offer_model
known_extensions
known_gaps
required_authority_classes
```

This prevents orchestration from assuming that all adapters implement the same commercial verbs.

## Vendor identifiers are mappings

Store vendor IDs with their scope and provenance: product code, offer ID, agreement ID, account ID, subscription ID, package ID, listing ID, entitlement ID, meter ID. Never substitute one of them for the canonical commercial identity merely because it is convenient for an SDK call.

## Error translation

SDK/network errors are preserved for diagnosis but normalized into canonical failure classes where possible:

```text
REFUSED:INVALID_ISSUER
REFUSED:SUBJECT_UNRESOLVED
REFUSED:STALE_EVENT
REFUSED:ILLEGAL_TRANSITION
REFUSED:AUTHORITY_MISSING
UNSUPPORTED:VENDOR_CAPABILITY
BLOCKED:VENDOR_PREREQUISITE
UNKNOWN:AMBIGUOUS_EXTERNAL_RESULT
```

Unknown vendor enum values must not fall through to success.

## Generation boundary

Wire types, mapping tables, schemas, intent constructors, and fixtures are excellent generation targets. The canonical transition system and authority policy remain shared source. This keeps new marketplaces cheap without pretending code generation proves runtime correctness.

## Operational exercise

Define one adapter interface that can support AWS SaaS, Microsoft SaaS, Google SaaS, Alibaba SPI SaaS, Salesforce licensing, and Red Hat container certification without using any one vendor's object as the canonical abstraction. Then list the vendor extensions that intentionally sit outside the shared interface.
