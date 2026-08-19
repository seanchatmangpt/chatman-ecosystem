
# 06 — Engagement timeline

All 10 phases of a real SOC2 Type II engagement lifecycle, in order. A
phase with no fact renders `NOT STARTED` — the timeline is complete by
construction, not by how much the consumer has filled in.

| # | Phase | Status | Started | Ended | Notes |
|---|---|---|---|---|---|
| AUDIT-BUNDLE-ASSEMBLY | 9: Evidence Bundle Assembly | NOT STARTED | — | — |  |
| AUDIT-COLLECTION-INIT | 5: Evidence Collection Period Initiation | not started | — | — | All 10 engagement-timeline phases (AUDIT-SCOPING through AUDIT-REPORT-HANDOFF) render NOT STARTED by construction where no prov:Activity PHASE-STATUS fact exists -- soc2/06-ENGAGEMENT-TIMELINE.md lines 8-19, generated build 975c7db/96301d6. Confirming the zero-recorded-status finding for the phases not otherwise marked below; this fact intentionally documents that absence rather than closing it. |
| AUDIT-CONTROL-DESIGN-DOC | 3: Control Design Documentation | NOT STARTED | — | — |  |
| AUDIT-DESIGN-EVAL | 4: Control Design Evaluation | NOT STARTED | — | — |  |
| AUDIT-EXCEPTION-ID | 7: Exception Identification | NOT STARTED | — | — |  |
| AUDIT-OE-TESTING | 6: Operating Effectiveness Testing | NOT STARTED | — | — |  |
| AUDIT-READINESS | 2: Readiness Assessment (Gap Analysis) | in progress | 2026-08-18 | — | Gap-analysis pass against real platform-console/autofde-lab-mcp source: new criterion findings confirmed for C1-1 and P8, exception remediation status re-verified for A1-1, CC3, CC6 (resolved), and CC9-1 against live evidence and git history. |
| AUDIT-REMEDIATION | 8: Management Response & Remediation | NOT STARTED | — | — |  |
| AUDIT-REPORT-HANDOFF | 10: Auditor Report Handoff (terminal — evidence bundle handed to a human auditor; no opinion produced here) | NOT STARTED | — | — |  |
| AUDIT-SCOPING | 1: Scoping & System Description | complete | 2026-08-18 | — | System description and system-boundary facts composed and generated into soc2/01-SYSTEM-DESCRIPTION.md (build 975c7db, regenerated 96301d6); scope of the SOC2 readiness binder's subject system established. |


## How to update a phase

```turtle
[] a prov:Activity ;
    dcterms:subject "AUDIT-OE-TESTING" ;
    skos:notation "PHASE-STATUS" ;
    skos:prefLabel "in progress" ;
    prov:startedAtTime "2026-08-01"^^xsd:date ;
    dcterms:description "Operating-effectiveness testing underway for CC6, CC7." .
```

