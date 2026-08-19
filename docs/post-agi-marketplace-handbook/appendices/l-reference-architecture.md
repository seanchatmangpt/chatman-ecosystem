# Appendix L — Reference Architecture

```mermaid
flowchart TD
    O[Observed product + marketplace contracts]
    Admit[Admission / O*]
    Graph[Canonical Commercial Graph]
    Ggen[ggen Manufacturing]
    Proj[Marketplace Projection]
    Gym[Gym / Contract Qualification]
    Intent[Immutable Commercial Intent]
    Broker[BRCE Authority Broker]
    Vendor[Marketplace / External System]
    Verify[Independent Postcondition Verification]
    Receipt[Receipt DAG]
    Replay[Replay / Reconstruction]
    Standing[Scoped Standing]

    O --> Admit --> Graph --> Ggen --> Proj
    Proj --> Gym
    Gym --> Intent
    Intent --> Broker --> Vendor
    Vendor --> Verify --> Receipt --> Replay --> Standing
    Receipt --> Graph
```

## Planes

### Semantic plane

Owns canonical product identity, plans, offers, agreements, entitlements, meters, deployment classes, support, security claims, and ontology.

### Projection plane

Owns vendor mapping rules, generated listing metadata, adapters, deployment packages, schemas, and vendor extensions.

### Runtime plane

Owns fulfillment, customer tenancy, usage observation, operational reliability, and support.

### Commercial plane

Owns offers, agreement state, entitlement transitions, meter submissions, settlement import, reconciliation, and channel attribution.

### Authority plane

Owns SELECT/CONSTRUCT/DO classification, exact grants, idempotency, and BRCE.

### Evidence plane

Owns receipts, content identity, provenance, replay, standing, and drift.

### Qualification plane

Owns structural checks, contract tests, gyms, differential testing, sandbox execution, live qualification, and falsifiers.

No plane receives ambient authority merely because it can observe another plane.
