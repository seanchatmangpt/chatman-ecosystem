# Documentation Inventory — v26.8.18

> Reviewed implementation baseline: `2d149b4091f6b5239ecfbbe054fdb0b2f5eb5f01`  
> Documentation branch subject: `docs/v26.8.18-repo-review`  
> Inventory standing: `PARTIAL_ALIVE` until the exact documentation head passes all applicable repository gates.

This is the repository-wide documentation map for the current operational release. It separates **what may be edited as current truth** from historical evidence, generated projections, and future-release doctrine.

## Lifecycle classes

| Class | Meaning | Edit rule |
|---|---|---|
| `CANONICAL` | constitutional or operational source of truth | edit deliberately; update dependent projections |
| `CURRENT` | current v26.8.18 operational explanation | keep synchronized with exact observed implementation |
| `HISTORICAL` | evidence captured at an earlier subject/time | preserve observations; append corrections rather than rewriting history |
| `GENERATED` | deterministic projection of canonical data | never hand-edit |
| `FUTURE` | v26.9.1 target/research/proof corpus | do not relabel as current implementation |
| `LOCAL` | component/package-specific operator or developer documentation | maintain with owning implementation surface |

## Repository-root documentation

| Path | Class | Purpose |
|---|---|---|
| `AGENTS.md` | CANONICAL | agent/release operating law |
| `CONSTITUTION.md` | CANONICAL | constitutional invariants and standing law |
| `CONTRIBUTING.md` | CURRENT | contribution and verification workflow |
| `README.md` | CURRENT | repository/release landing page |
| `ROADMAP.md` | CURRENT | current frontier and next evidence-changing work |
| `SESSION-FINAL-STATUS.md` | CURRENT | bounded v26.8.18 status receipt |
| `ECOSYSTEM-INTEGRATION-REVIEW.md` | HISTORICAL | integration review evidence from its observed subject |
| `SONY-READINESS-GAP-CLOSURE.md` | HISTORICAL | enterprise-readiness gap review/evidence |
| `SONY-SVP-REVIEW-CLOSURE.md` | HISTORICAL | executive-buyer review/evidence |

## Current operational documentation

These documents describe the current v26.8.18 subject and should move when the implementation boundary moves:

- `docs/v26.8.18-release.md`
- `docs/ARCHITECTURE.md`
- `docs/OPERATIONS.md`
- `docs/DOCUMENTATION-INVENTORY.md`
- `docs/VERSIONING.md`
- `docs/API-SURFACES.md`
- `docs/OBSERVABILITY.md`
- `docs/OCEL-PROCESS-EVIDENCE.md`
- `docs/GGEN-SERVICE.md`
- `docs/SECURITY-MODEL.md`
- `docs/RELIABILITY-AND-DR.md`
- `docs/TROUBLESHOOTING.md`
- `docs/RELEASE-PROCESS.md`
- `docs/DEVELOPMENT.md`
- `docs/DOCS-MAINTENANCE.md`
- `docs/README.md`
- `docs/SUMMARY.md`
- `docs/00-introduction.md`
- `docs/00-reading-map.md`

## Constitutional, manufacturing, flow, research, and TPS corpus

The numbered mdBook corpus is long-form doctrine/research. These files are authored documents, not generated projections. Version-specific release claims inside them remain subject to the distinction in `docs/VERSIONING.md`.

### 01–20

- `docs/01-constitutional-thesis.md`
- `docs/02-chatman-equation.md`
- `docs/03-ontological-stratification.md`
- `docs/04-contextual-execution.md`
- `docs/05-non-collapse-algebra.md`
- `docs/06-candidate-manufacture.md`
- `docs/07-dual-admission-geometry.md`
- `docs/08-refusal-as-type.md`
- `docs/09-brce-no-unreceipted-actuation.md`
- `docs/10-receipt-bifurcation.md`
- `docs/11-mandatory-factorization.md`
- `docs/12-semantic-manufacturing.md`
- `docs/13-projection-contracts.md`
- `docs/14-representation-fiber.md`
- `docs/15-reverse-semantic-morphism.md`
- `docs/16-semantic-ci.md`
- `docs/17-recursive-non-self-certification.md`
- `docs/18-four-closure-obligations.md`
- `docs/19-epistemic-crown.md`
- `docs/20-representational-crown.md`

### 21–40

- `docs/21-operational-crown.md`
- `docs/22-class-closure-crown.md`
- `docs/23-class-quotient.md`
- `docs/24-definition-of-done-lattice.md`
- `docs/25-crown-receipt-manifest.md`
- `docs/26-release-theorem.md`
- `docs/27-standing-algebra.md`
- `docs/28-anti-wip-governance.md`
- `docs/29-manufactured-complexity.md`
- `docs/30-constitutional-compression.md`
- `docs/31-work-necessity-test.md`
- `docs/32-eliminate-automate-accelerate.md`
- `docs/33-littles-law-arrivals.md`
- `docs/34-information-theory.md`
- `docs/35-dfcm-maximal-reversible.md`
- `docs/36-authority-as-reachability.md`
- `docs/37-security-non-reachability.md`
- `docs/38-organization-semantic-manifold.md`
- `docs/39-process-is-state.md`
- `docs/40-ggen-semantic-manufacturing-system.md`

### 41–60

- `docs/41-ggen-marketplace-civilization-memory.md`
- `docs/42-ggen-legacy-epistemic-fence.md`
- `docs/43-repository-ontology.md`
- `docs/44-clay-substrate-equivalence.md`
- `docs/45-post-agi-limit.md`
- `docs/46-post-agi-cjk.md`
- `docs/47-post-agi-swarm-protocol.md`
- `docs/48-crown-experiment-protocol.md`
- `docs/49-working-backwards-release.md`
- `docs/50-civilization-scale-synthesis.md`
- `docs/51-ecosystem-map.md`
- `docs/52-repository-atlas.md`
- `docs/53-month-in-review.md`
- `docs/54-current-standing.md`
- `docs/55-pull-system.md`
- `docs/56-receipts-replay-evidence.md`
- `docs/57-operating-control-plane.md`
- `docs/58-falsifiers-open-work.md`
- `docs/59-roadmap-autonomous-factory.md`
- `docs/60-ecosystem-synthesis.md`

### 61–80

- `docs/61-research-program.md`
- `docs/62-axiomatic-kernel.md`
- `docs/63-categorical-semantics.md`
- `docs/64-epistemic-standing.md`
- `docs/65-process-calculus.md`
- `docs/66-dfcm-search-geometry.md`
- `docs/67-authority-security-theorems.md`
- `docs/68-flow-economics.md`
- `docs/69-experimental-method.md`
- `docs/70-dissertation-synthesis.md`
- `docs/71-tps-production-constitution.md`
- `docs/72-machine-scale-throughput.md`
- `docs/73-latent-poc-reservoir.md`
- `docs/74-portfolio-pull-control.md`
- `docs/75-jidoka-andon-pokayoke.md`
- `docs/76-heijunka-capacity.md`
- `docs/77-standard-work-ggen.md`
- `docs/78-kaizen-self-improving-factory.md`
- `docs/79-factory-metrics.md`
- `docs/80-post-operator-factory.md`

## Platform Engineer's Handbook bridge documents

- `docs/platform-engineers-handbook-ggen-packs.md`
- `docs/platform-engineers-handbook-colima-runtime.md`
- `docs/platform-engineers-handbook-backward-chain.md`
- `docs/platform-engineers-handbook-backport.md`
- `docs/platform-engineers-handbook-capability-roadmap.md`

## Post-AGI Platform Engineer's Handbook

The handbook is its own complete nested book. Its authoritative nested file list is `docs/post-agi-platform-handbook/SUMMARY.md`. The repository contains:

- root: `README.md`, `SUMMARY.md`, `working-backwards.md`, `preface.md`, `how-to-read.md`, `notation.md`;
- chapters 1–65 across `part-01-epistemic-closure/` through `part-16-complete-calculus/`;
- appendices `a-formal-notation.md` through `p-civilization-memory-algebra.md`;
- `epilogue.md`.

Every nested handbook chapter is included by `docs/SUMMARY.md`; the nested summary is the canonical exhaustive index for that sub-book.

## v26.8.18 ggen work package

These are current design-to-implementation records and are reconciled against v26.8.18 implementation evidence:

- `docs/jira/v26.8.18/00-OVERVIEW.md`
- `docs/jira/v26.8.18/01-GGEN-AS-IAAS.md`
- `docs/jira/v26.8.18/02-GGEN-AS-PAAS.md`
- `docs/jira/v26.8.18/03-GGEN-AS-SAAS.md`
- `docs/jira/v26.8.18/04-GGEN-BRCE-CROSS-CUTTING.md`

## Historical audits

Preserve these as time-bounded evidence:

- `docs/audits/2026-08-08-stubs-wip.md`
- `docs/audits/2026-08-15-stubs-wip.md`

## v26.9.1 frozen proof corpus

`docs/v26.9.1/00_CANONICAL_INDEX.md` is the authoritative exhaustive index for the frozen v26.9.1 constitutional corpus and its documents 01–49. That corpus is `FUTURE` relative to the v26.8.18 operational snapshot. Its architecture/mathematics must not be rewritten merely because current implementation differs.

## Platform-console local documentation

These are owned by the deployable platform surface:

- `platform-console/README.md`
- `platform-console/docs/DATA-RESIDENCY.md`
- `platform-console/docs/DISASTER-RECOVERY.md`
- `platform-console/docs/DR-SECOND-CLUSTER.md`
- `platform-console/docs/INCIDENT-COMMUNICATION-TEMPLATE.md`
- `platform-console/docs/SCOPE-AND-LIMITATIONS.md`
- `platform-console/docs/SOC2-CONTROL-MAPPING.md`
- `platform-console/docs/SUPPORT-AND-ESCALATION.md`

## Generated documentation/projections

The following documentation-like outputs are projections and must not be manually corrected:

- `views/generated/*.md`
- `status/README.md`
- `status/repos/*.md`
- generated `soc2/*.md`
- generated status-deck/output artifacts where applicable

Fix their canonical input or generator and regenerate.

## Registry rule

`catalog/documents.toml` is the explicit registry for cross-cutting documents used by the control plane. It is **not** intended to enumerate every chapter or package-local README. Add a registry entry when a document becomes a cross-cutting constitutional, operational, release, or operator contract.

## Completeness falsifiers

This inventory is stale if any of the following becomes true:

1. a new cross-cutting doc is added without classification;
2. a current operational doc points at a superseded exact subject without saying so;
3. a historical audit is rewritten as current evidence;
4. generated Markdown is hand-edited instead of regenerated;
5. v26.9.1 target doctrine is relabeled as v26.8.18 implementation state;
6. a new operator-visible capability ships with no owning operational documentation or explicit declaration that an existing document covers it.
