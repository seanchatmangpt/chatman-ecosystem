# 30. Security as a Commercial Capability

## Security claims are product promises

Once a buyer evaluates security during procurement, controls become part of the commercial product. “Encryption,” “tenant isolation,” “private connectivity,” “customer-managed keys,” “least privilege,” and “supply-chain security” must map to exact implementations and evidence—not persuasive questionnaire prose.

```text
SecurityClaim =
  Control
  × ExactSubject
  × Verifier
  × FreshEvidence
  × Scope
```

If any factor is missing, the claim is `UNKNOWN` or narrower than the marketing statement.

## Controls before questionnaires

A mature platform should make security evidence a by-product of normal operation:

- workload identity and least-privilege policy;
- secrets lifecycle and rotation;
- encryption-in-transit and at-rest configuration;
- tenant isolation tests;
- network-policy and private-endpoint evidence;
- SBOM and exact artifact digest;
- image/package vulnerability results;
- provenance/signature chain;
- audit trails for privileged changes;
- incident evidence and response timing.

The questionnaire is a projection of this graph.

## Customer-managed keys

CMK is a useful example of semantic precision. Provider-managed encryption, dedicated keys, customer-controlled key-encryption keys, and true customer-held cryptographic control are not equivalent. The product must state which boundary actually exists.

A marketplace projection cannot upgrade that security standing through wording.

## Private connectivity

TLS over the public internet is secure transport, but it is not a private network path. If a Fortune 5 buyer requires private service connectivity, the product needs a real topology and verification showing data plane/control plane dependencies stay inside the admitted boundary.

## Supply-chain evidence follows the exact artifact

A scan result on image digest `A` does not prove digest `B`. A Salesforce security review on package version `1.2` does not automatically prove `1.3`. Red Hat certification for a container does not prove a later tag.

Evidence reuse requires exact identity or a separate equivalence proof.

## Exceptions require authority and expiry

If a buyer accepts a compensating control, the exception should identify affected claim, customer, authority, rationale, evidence, effective interval, and re-evaluation date. It is not a global weakening of product policy.

## Refusals

- `REFUSED:SECURITY_BY_QUESTIONNAIRE`
- `REFUSED:CMK_CLAIM_WITHOUT_CUSTOMER_CONTROL_BOUNDARY`
- `REFUSED:TLS_AS_PRIVATE_CONNECTIVITY`
- `REFUSED:STALE_SCAN_FOR_NEW_ARTIFACT`
- `REFUSED:SECURITY_CONTROL_DROPPED_FOR_MARKETPLACE_PACKAGING`

## Operational exercise

Select ten security claims likely to appear in Fortune 5 procurement. For each, record canonical claim, implementation control, exact subject, verifier, evidence freshness, marketplace projection, customer-visible wording, and falsifier. Any claim that cannot be linked to a runtime control stays `UNKNOWN`.
