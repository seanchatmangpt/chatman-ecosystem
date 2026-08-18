
# 06 — Engagement timeline

All 10 phases of a real SOC2 Type II engagement lifecycle, in order. A
phase with no fact renders `NOT STARTED` — the timeline is complete by
construction, not by how much the consumer has filled in.

| # | Phase | Status | Started | Ended | Notes |
|---|---|---|---|---|---|
| AUDIT-BUNDLE-ASSEMBLY | 9: Evidence Bundle Assembly | NOT STARTED | — | — |  |
| AUDIT-COLLECTION-INIT | 5: Evidence Collection Period Initiation | NOT STARTED | — | — |  |
| AUDIT-CONTROL-DESIGN-DOC | 3: Control Design Documentation | NOT STARTED | — | — |  |
| AUDIT-DESIGN-EVAL | 4: Control Design Evaluation | NOT STARTED | — | — |  |
| AUDIT-EXCEPTION-ID | 7: Exception Identification | NOT STARTED | — | — |  |
| AUDIT-OE-TESTING | 6: Operating Effectiveness Testing | NOT STARTED | — | — |  |
| AUDIT-READINESS | 2: Readiness Assessment (Gap Analysis) | NOT STARTED | — | — |  |
| AUDIT-REMEDIATION | 8: Management Response & Remediation | NOT STARTED | — | — |  |
| AUDIT-REPORT-HANDOFF | 10: Auditor Report Handoff (terminal — evidence bundle handed to a human auditor; no opinion produced here) | NOT STARTED | — | — |  |
| AUDIT-SCOPING | 1: Scoping & System Description | NOT STARTED | — | — |  |


## How to update a phase

```turtle
[] a prov:Activity ;
    dcterms:subject "AUDIT-OE-TESTING" ;
    skos:notation "PHASE-STATUS" ;
    skos:prefLabel "in progress" ;
    prov:startedAtTime "2026-08-01"^^xsd:date ;
    dcterms:description "Operating-effectiveness testing underway for CC6, CC7." .
```

