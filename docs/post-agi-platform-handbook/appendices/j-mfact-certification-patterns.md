# Appendix J — mfact Certification Patterns

mfact-style certification should turn evidence into a machine-checkable standing claim.

## Candidate certificate

Bind exact artifact identity to construction inputs and validator results.

## Subject certificate

Bind exact subject identity to observed execution evidence.

## Class certificate

Bind class identity, equivalence relation, parameterized manufacture, historical instances, and falsifiers.

## Transfer certificate

State why previously validated verifier or class evidence is applicable to the current exact subject.

## Certification rule

Certification records a claim and its evidence. It does not manufacture authority. A certified candidate still crosses BRCE before consequential DO.

<!-- semantic-enrichment:v1 -->

## Operational significance

**Appendix J — mfact Certification Patterns** is not retained as a label-only reference. Formal admission separates a generated claim from a mechanically checked invariant. The useful pattern is `ggen renders; Lean admits; mfact certifies`: generation constructs a candidate, a proof system checks a precisely stated property, and certification binds the checked claim to the exact artifact identity. A theorem about an abstract model is not automatically a theorem about the deployed artifact; the correspondence edge must be explicit.

## System contract

Formal properties should focus on consequences that are expensive to discover at runtime: conservation, authority non-escalation, state-machine reachability, receipt completeness, bounded resource use, and impossibility of forbidden transitions. Assumptions belong in the theorem interface rather than prose footnotes. If the proof relies on an admitted constant or model approximation, that dependency becomes part of the receipt.

## Failure modes and falsifiers

The critical falsifier is correspondence failure: the proved object differs from the generated or executed subject. Other failures include `sorry`/axiom escape hatches, unbound external assumptions, or a certificate that can be replayed against a changed artifact. Certification therefore binds theorem identity, checker/toolchain identity, artifact digest, assumptions, and verification result.

## Evidence before promotion

For this subject, promotion requires evidence that intersects the claim: exact subject identity, the admitted inputs or assumptions, the verifier or observation boundary, and a reproducible result. Static structure can establish representational closure; simulated execution can establish bounded behavior; neither is silently promoted to real-world consequential standing. A changed subject, stale observation, failed replay, unresolved contradiction, or verifier that no longer intersects the claim revokes the prior standing and requires re-admission.
