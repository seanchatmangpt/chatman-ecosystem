# Documentation Index — current head plus preserved release snapshots

This is the landing page for the Chatman Ecosystem documentation corpus.

> **Current implementation baseline for this review:** `be27c93621ef494ccc342e0dc36c99dab9e391a6`  
> **Preserved operational release snapshot:** `v26.8.18` at `2d149b4091f6b5239ecfbbe054fdb0b2f5eb5f01`  
> **Repository-wide Crown:** not asserted by this documentation update  
> **Future proof corpus:** `v26.9.1`

The v26.8.18 pages remain historical evidence for that exact release. They are **not** a complete description of capabilities merged after that baseline. Current capability pages must name their own executable source and evidence boundary.

## Start here

- [Documentation Inventory](DOCUMENTATION-INVENTORY.md) — corpus lifecycle, currentness, editability, generated-source rules, and the relevant documentation census.
- [How to Read This Documentation](00-reading-map.md) — Diátaxis-aware reading paths.
- [v26.8.18 Release Snapshot](v26.8.18-release.md) — preserved release evidence; historical for post-baseline capabilities.
- [Architecture](ARCHITECTURE.md) and [Operations and Admission](OPERATIONS.md) — cross-cutting architecture/operations at their stated subjects.
- [Versioning](VERSIONING.md) — version/currentness rules.

## Current Diátaxis: replicated evidence state

A new operator-visible subsystem merged after the v26.8.18 snapshot. Its current operational documentation is split by reader need rather than duplicated across one omnibus page:

| Need | Diátaxis role | Authoritative page |
|---|---|---|
| learn the bounded happy path | Tutorial | [Replicated Evidence State — Tutorial](diataxis/tutorials/replicated-evidence-state.md) |
| qualify or diagnose replica evidence | How-to | [Qualify Replicated Evidence](diataxis/how-to/qualify-replicated-evidence.md) |
| exact APIs, states, refusals, schemas, limits | Reference | [Replicated Evidence State — Reference](diataxis/reference/replicated-evidence-state.md) |
| understand quorum/currentness/authority rationale | Explanation | [Why Replicated Evidence Stops at PARTIAL_ALIVE](diataxis/explanation/replicated-evidence-currentness.md) |

The **Reference** page is the canonical home for factual subsystem contracts. Tutorial, how-to, and explanation pages link to it instead of maintaining parallel truth tables.

## Preserved v26.8.18 operator documentation

These pages remain useful for the v26.8.18 subject but must not be interpreted as exhaustive current-head coverage:

| Area | Document |
|---|---|
| release boundary | [v26.8.18 Release Snapshot](v26.8.18-release.md) |
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

The main mdBook contains the numbered constitutional/manufacturing/research corpus plus nested books. `SUMMARY.md` remains the authored publication graph. Its `Current v26.8.18 Operations` section names the preserved release-era set; use this index and the documentation inventory for post-baseline currentness.

## Post-AGI Platform Engineer's Handbook

The nested handbook has its own exhaustive reading order:

- [Handbook home](post-agi-platform-handbook/README.md)
- [Nested summary](post-agi-platform-handbook/SUMMARY.md)

It is doctrine/reference material, not evidence that a current runtime capability executed.

## v26.8.18 ggen work package

The design-to-implementation records are preserved for their stated release subject:

- [Overview](jira/v26.8.18/00-OVERVIEW.md)
- [ggen as IaaS](jira/v26.8.18/01-GGEN-AS-IAAS.md)
- [ggen as PaaS](jira/v26.8.18/02-GGEN-AS-PAAS.md)
- [ggen as SaaS](jira/v26.8.18/03-GGEN-AS-SAAS.md)
- [BRCE cross-cutting law](jira/v26.8.18/04-GGEN-BRCE-CROSS-CUTTING.md)

## Historical evidence

Dated audits under `audits/`, root gap reviews, and exact release snapshots are historical evidence. Preserve their original observation; add current pointers rather than rewriting history.

## v26.9.1 frozen proof corpus

[`v26.9.1/00_CANONICAL_INDEX.md`](v26.9.1/00_CANONICAL_INDEX.md) is the frozen next-release constitutional/proof corpus. It is a target/specification corpus unless a page supplies exact execution evidence; it must not be used as proof of current runtime standing.

## Platform-console local docs

The deployable console owns concrete operator/procurement/runbook docs under `../platform-console/docs/`. Cross-cutting pages link to those instead of duplicating component contracts.

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
