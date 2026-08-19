# 51. Differential Marketplace Testing

## Compare commercial meaning, not raw payloads

The purpose of differential testing is to determine whether two marketplace projections preserve the same canonical semantics under equivalent scenarios.

Raw HTTP requests will differ. Vendor event order can differ. Listing identifiers and settlement formats differ. Those are expected. The comparison target is normalized customer meaning.

```text
π_c(trace_market_1) ≡ π_c(trace_market_2)
within declared projection bounds
```

## Canonical scenario

Start with one product version, plan, organization, price semantics, usage definition, support policy, and deployment class. Compile the scenario into each marketplace gym or sandbox:

```text
purchase
→ activate
→ fulfill
→ usage
→ meter
→ change plan
→ cancel
```

Then normalize observations back into canonical agreement, entitlement, fulfillment, usage, and financial state.

## Expected divergence

Differences can be legitimate:

- one market supports a longer contract term;
- one supports a richer private-offer feature;
- one requires explicit activation while another auto-activates;
- one settlement file arrives on a different cadence;
- one package format exposes a vendor-specific resource.

The test records these as projection extensions or narrower mappings.

## Unexpected divergence

A defect is a difference with no admitted explanation:

- same plan grants different features;
- cancellation revokes at different effective times without a contract difference;
- usage unit changes between markets;
- support tier differs;
- one path retains data longer without a policy difference;
- one meter double-counts a retry.

Differential testing finds semantic drift that unit tests inside each adapter cannot see.

## Align exact subjects

Use the same canonical product/plan version and the corresponding exact adapter/pack versions. Comparing AWS v2 integration against Microsoft v3 product semantics can create false differences.

The comparison receipt binds every source identity.

## Projection loss

When equivalence is impossible, the test should prove the declared loss rather than fail generically. For example, a market may not support the canonical private-offer amendment class. The normalized result can be `UNSUPPORTED` for that capability while entitlement behavior remains equivalent.

## Refusals

- `REFUSED:RAW_PAYLOAD_EQUALITY_AS_SEMANTIC_TEST`
- `REFUSED:KNOWN_VENDOR_EXTENSION_AS_DEFECT`
- `REFUSED:UNEXPLAINED_RIGHTS_DIVERGENCE`
- `REFUSED:DIFFERENT_PRODUCT_VERSIONS_AS_COMPARABLE_SUBJECTS`
- `REFUSED:PROJECTION_LOSS_HIDDEN`

## Operational exercise

Execute equivalent lifecycle scenarios through two marketplace projections. Compare canonical states at every transition, not only the final state. Produce a report that classifies every divergence as expected extension, narrowing/loss, unsupported, timing-only, or defect.
