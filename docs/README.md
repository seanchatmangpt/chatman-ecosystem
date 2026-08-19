# Documentation Index — v26.8.18

This is the landing page for the Chatman Ecosystem documentation corpus.

> **Current operational snapshot:** `v26.8.18`  
> **Reviewed implementation baseline:** `2d149b4091f6b5239ecfbbe054fdb0b2f5eb5f01`  
> **Ecosystem standing:** `PARTIAL_ALIVE`  
> **Next composition crown:** `v26.9.1`

## Start here

- [Documentation Inventory](DOCUMENTATION-INVENTORY.md) — complete corpus map, lifecycle class, editability and source-of-truth rules.
- [v26.8.18 Release Snapshot](v26.8.18-release.md) — bounded current operational state.
- [Architecture](ARCHITECTURE.md) — current system layers and boundaries.
- [Operations and Admission](OPERATIONS.md) — current operator/admission model.
- [How to Read This Book](00-reading-map.md) — reading paths through the long-form corpus.
- [Versioning](VERSIONING.md) — why v26.8.18 and v26.9.1 coexist without collapsing.

## v26.8.18 operator documentation

| Area | Document |
|---|---|
| interfaces and authority | [API and Capability Surfaces](API-SURFACES.md) |
| metrics/traces/logs | [Observability](OBSERVABILITY.md) |
| process evidence | [OCEL Process Evidence](OCEL-PROCESS-EVIDENCE.md) |
| semantic manufacture service | [ggen Service Contract](GGEN-SERVICE.md) |
| identity/network/admission/security | [Security Model](SECURITY-MODEL.md) |
| failure domains/recovery | [Reliability and Disaster Recovery](RELIABILITY-AND-DR.md) |
| known failure modes | [Troubleshooting](TROUBLESHOOTING.md) |
| release mechanics | [Release Process](RELEASE-PROCESS.md) |
| engineering verification | [Development Guide](DEVELOPMENT.md) |
| maintaining the corpus | [Documentation Maintenance](DOCS-MAINTENANCE.md) |

## Long-form corpus

The main mdBook contains **80 numbered chapters** spanning constitutional law, semantic manufacture, evidence/closure, DfCM, authority/security, process intelligence, repository realizations, post-AGI substrate independence, factory/TPS economics and the research program.

Use [`SUMMARY.md`](SUMMARY.md) as the authoritative publication order. Chapters 01–80 are individually enumerated in [`DOCUMENTATION-INVENTORY.md`](DOCUMENTATION-INVENTORY.md).

## Post-AGI Platform Engineer's Handbook

The nested handbook is a complete 65-chapter + 16-appendix book:

- [Handbook home](post-agi-platform-handbook/README.md)
- [Nested exhaustive summary](post-agi-platform-handbook/SUMMARY.md)

It is included in the main mdBook publication graph but maintains its own internal reading order.

## v26.8.18 ggen work package

The original IaaS/PaaS/SaaS design tickets have been reconciled against the implementation that actually landed:

- [Overview](jira/v26.8.18/00-OVERVIEW.md)
- [ggen as IaaS](jira/v26.8.18/01-GGEN-AS-IAAS.md)
- [ggen as PaaS](jira/v26.8.18/02-GGEN-AS-PAAS.md)
- [ggen as SaaS](jira/v26.8.18/03-GGEN-AS-SAAS.md)
- [BRCE cross-cutting law](jira/v26.8.18/04-GGEN-BRCE-CROSS-CUTTING.md)

These documents distinguish observed implementation from remaining gaps instead of preserving contradictory proposal-era “stub” language.

## Historical evidence

Dated audits under [`audits/`](audits/) and root gap-review documents are historical evidence. Do not rewrite their original observation to match the current head; add current pointers when later work closes a gap.

## v26.9.1 frozen proof corpus

[`v26.9.1/00_CANONICAL_INDEX.md`](v26.9.1/00_CANONICAL_INDEX.md) is the authoritative entry point for the frozen next-release constitutional/proof corpus. It is a **future target** relative to v26.8.18, not a current operational snapshot.

## Platform-console local docs

The deployable console has its own concrete operator/procurement/runbook docs under [`../platform-console/docs/`](../platform-console/docs/) covering scope/limitations, data residency, DR, second-cluster cold standby, incident communications, SOC 2 control mapping, and support/escalation. The cross-cutting docs in this directory link to those rather than duplicating all module detail.

## Generated documentation

Do not hand-edit:

- `../views/generated/*.md`
- `../status/README.md`
- `../status/repos/*.md`
- generated `../soc2/*.md`

Repair canonical input/generator and regenerate. See [Documentation Maintenance](DOCS-MAINTENANCE.md).

## Governing documents

- [`../AGENTS.md`](../AGENTS.md) — operating/release law
- [`../CONSTITUTION.md`](../CONSTITUTION.md) — constitutional authority/standing law
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — contributor workflow
