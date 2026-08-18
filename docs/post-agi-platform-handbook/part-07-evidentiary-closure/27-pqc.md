# 27. Post-Quantum Receipt Chains

Civilization memory is only useful if its evidence can survive longer than the infrastructure generation that created it.

For receipts expected to remain meaningful across cryptographic eras, the ecosystem should separate three concerns:

1. content identity;
2. authenticated origin and authorization;
3. long-lived verification policy.

## Post-quantum primitives

A post-quantum profile can incorporate standardized families such as ML-KEM for key establishment and ML-DSA or SLH-DSA for digital signatures where their properties fit the use case.

The choice of algorithm is not constitutional. The constitutional requirement is that cryptographic identity and authority bindings remain explicit and replaceable as standards evolve.

## Crypto agility is part of reconstitution

Receipts should not encode “this exact algorithm forever” as semantic truth.

Instead, the receipt identifies:

- algorithm and parameters used at creation;
- public-key identity or trust anchor;
- signed statement or canonical digest;
- validation policy;
- any later re-attestation or migration chain.

This permits evidence to be renewed without pretending the original signature was created under a later algorithm.

## Long-lived evidence requires context

A signature can prove that a key signed a statement. It cannot independently prove that the key was authorized for the subject at that historical time.

The receipt DAG therefore also preserves policy, delegation, and authority context.

Post-quantum cryptography protects one layer of the evidence chain; it does not replace constitutional semantics.

## Hybrid transitions

During cryptographic migrations, a system may use hybrid signatures or parallel attestations. The evidence graph should represent both rather than collapsing them into one opaque `verified=true` bit.

This makes later policy decisions possible without rewriting history.

## Falsifier

A receipt architecture is not cryptographically agile if replacing an algorithm changes the semantic identity of the underlying operation or destroys the ability to verify historical receipts.

## Operational exercise

Take a long-lived receipt schema and identify which fields are cryptographic mechanism, which are semantic identity, and which are authority. Refactor the schema so the mechanism can evolve without erasing the original proposition.