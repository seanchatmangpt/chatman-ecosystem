# Security Model — v26.8.18

## Security invariant

The ecosystem models security primarily as **non-reachability of forbidden consequential transitions**. Authentication, RBAC, mTLS, NetworkPolicy, admission controls, scanning, receipts and audit evidence are independent fences; none substitutes for BRCE authority.

```text
untrusted observation
  -> identify subject
  -> authenticate
  -> authorize capability
  -> validate policy/constraints
  -> construct candidate
  -> authority admission
  -> BRCE
  -> consequence + receipt
```

A credential proves possession of a capability credential. It does not grant authority outside the policy relation attached to that subject/action.

## Identity and authentication

The platform has multiple observed authentication paths including local-admin/session behavior and an external OIDC federation shape. The OIDC path exercises authorization-code/PKCE/JWKS/signature verification against a real standards-compliant IdP implementation.

Claim ceiling: this demonstrates a real OIDC federation mechanism, not that the local environment is a production tenant of a particular commercial identity provider.

## Authorization

Sensitive HTTP routes use role checks; Kubernetes-facing operations are additionally bounded by service-account/RBAC permissions. Authorization must be checked server-side. Hiding a button in the UI is not an authorization control.

Rules:

- viewer/read surfaces cannot inherit owner mutation authority;
- GitOps visibility does not imply Flux mutation authority;
- project ownership does not imply cluster-admin authority;
- repository ownership/credentials do not imply merge/release/production authority;
- telemetry data never carries authority merely through attributes.

## Network isolation and mTLS

The local cluster uses NetworkPolicy and Istio STRICT peer authentication on the admitted mesh paths. Live negative connectivity tests established that disallowed paths can be dropped rather than merely represented as policy objects.

A real failure was discovered when default-deny egress prevented injected sidecars from reaching DNS/istiod. The repair added narrowly scoped DNS/istiod egress rather than disabling policy globally.

The current topology is still single-node. Real cryptographic/network enforcement on one node does not imply multi-region trust distribution or partition tolerance.

## Admission policy

Kubernetes ValidatingAdmissionPolicy/CEL is used for selected fail-closed resource rules, including required resource declarations. Critical vulnerability policy also participates in the observed admission posture.

Admission policy is a precondition to Kubernetes acceptance. It is not evidence that the admitted workload later behaved correctly; runtime consequence still requires observation.

## Vulnerability scanning

Trivy was exercised against real images and produced non-zero findings, including a positive-control old image. This proves the scanner detects findings; it does not prove every image is vulnerability-free.

A security gate must preserve this distinction:

```text
scanner ran + findings observed
!= no vulnerabilities
!= risk accepted
!= deployment authorized
```

## Secrets and key material

The local cluster has evidence for etcd secret-envelope encryption work, but key topology and single-machine failure-domain limitations remain disclosed. ggen signing-key material has its own service-specific durability/custody ceiling described in `GGEN-SERVICE.md`.

No documentation may convert “encrypted at rest in this local configuration” into a general KMS/HSM or regulatory guarantee.

## Audit evidence

The platform records structured audit activity and has tamper-evident/hash-chain mechanisms for selected audit evidence. Audit records show observations about actions; they do not legalize unauthorized actions after the fact.

Required sequence remains:

```text
authorize before DO
receipt during/after lawful DO
observe consequence
retain audit evidence
```

not:

```text
DO first -> log it -> infer authority
```

## Storage and content delivery

Signed/expiring storage URLs are present as a content-access primitive. Their correctness depends on signature verification, expiry enforcement and object identity; they do not establish SaaS billing/entitlement by themselves.

## Observability receiver security

An earlier static Endpoints configuration created an unintended mesh-to-host OTLP route. The endpoint was removed and future OTLP ingress was constrained. This is an important architectural rule: observability plumbing must not create an alternate unauthenticated network escape path around application policy.

## Castle / adversarial construction

Castle is intentionally exposed with an allowlisted verb surface. Planner/search capability stays separate from authority. Goal models, adversarial worlds and CONSTRUCT artifacts may explore attack structure without granting a red-team actuation path.

## Compliance boundary

The repository contains SOC 2 readiness/control-mapping artifacts. These are evidence organization and gap-analysis mechanisms. They are **not**:

- a SOC 2 report;
- an auditor opinion;
- certification or attestation;
- proof of an observation period by an independent CPA firm.

Any compliance verdict must remain structurally refused unless the required external authority/evidence exists.

## Threat classes that must fail closed

- unauthenticated/expired session;
- insufficient role;
- cross-tenant namespace/workspace access;
- tampered receipt/digest/signature;
- stale or replayed authority token outside its admitted identity;
- undeclared WASM import/capability;
- unauthorized Kubernetes resource shape;
- unsafe image beyond admitted vulnerability policy;
- malicious telemetry/OCEL content attempting command injection;
- model/planner output attempting to self-authorize;
- generated document attempting to overwrite canonical policy.

## Standing rule

A security control is `ALIVE` only for the exact subject and behavior actually executed. Policy text, manifests, schemas and diagrams are valuable construction evidence but do not alone establish enforcement standing.
