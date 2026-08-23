# Documentation Inventory — current head and preserved snapshots

> Reviewed repository subject: `seanchatmangpt/chatman-ecosystem@be27c93621ef494ccc342e0dc36c99dab9e391a6`  
> Preserved release baseline: `v26.8.18@2d149b4091f6b5239ecfbbe054fdb0b2f5eb5f01`  
> Inventory standing: `PARTIAL_ALIVE` until the documentation change itself passes exact-head repository gates.

This inventory is the repository-wide currentness and ownership map. It deliberately separates current capability documentation from historical release evidence, doctrine, generated projections, and future proof targets.

## Lifecycle classes

| Class | Meaning | Edit rule |
|---|---|---|
| `CANONICAL` | constitutional/operational source of truth | edit deliberately; update dependent projections |
| `CURRENT` | current-head capability documentation grounded in executable behavior | change with the owning capability and evidence |
| `HISTORICAL` | evidence captured for an earlier exact subject/release | preserve observation; add pointers, do not rewrite history |
| `DOCTRINE` | long-form architecture/research/constitutional explanation | do not use as execution evidence |
| `GENERATED` | deterministic projection of canonical data | never hand-edit |
| `FUTURE` | target/release-proof corpus not yet established as current runtime | never relabel as current evidence |
| `LOCAL` | package/component-owned docs | maintain with owning implementation |

## Complete relevant documentation census

The census inspected the user-facing surfaces that can materially describe behavior, including repository-root Markdown; `docs/`; mdBook navigation (`book.toml`, `docs/SUMMARY.md`); tutorials/how-to/reference/explanation material; architecture, operations, API, observability, OCEL, ggen, security, reliability, troubleshooting, development, release, versioning and docs-maintenance pages; JIRA/release records; audits; nested handbooks/books; platform-console operator docs; generated status/views/SOC2 projections; `catalog/documents.toml`; package source/tests/workflows for replicated evidence; and examples embedded in those executable surfaces.

### Repository-root documentation

| Surface | Class | Currentness rule |
|---|---|---|
| `AGENTS.md` | CANONICAL | agent/release operating law |
| `CONSTITUTION.md` | CANONICAL | constitutional authority/standing law |
| `CONTRIBUTING.md` | CURRENT | contribution workflow at its stated commands |
| `README.md`, `ROADMAP.md` | CURRENT | landing/frontier; claims require exact evidence |
| `SESSION-FINAL-STATUS.md` | HISTORICAL | v26.8.18 bounded status receipt |
| `ECOSYSTEM-INTEGRATION-REVIEW.md`, `SONY-READINESS-GAP-CLOSURE.md`, `SONY-SVP-REVIEW-CLOSURE.md` | HISTORICAL | dated review evidence |

### Current Diátaxis capability documentation

The replicated-evidence subsystem is the post-v26.8.18 operator-visible capability that triggered this census. Its documentation ownership is now explicit:

| Path | Role | Class |
|---|---|---|
| `docs/diataxis/tutorials/replicated-evidence-state.md` | Tutorial — bounded successful learning path | CURRENT |
| `docs/diataxis/how-to/qualify-replicated-evidence.md` | How-to — qualification and diagnosis procedures | CURRENT |
| `docs/diataxis/reference/replicated-evidence-state.md` | Reference — canonical factual contract | CURRENT |
| `docs/diataxis/explanation/replicated-evidence-currentness.md` | Explanation — standing/authority rationale | CURRENT |

Canonical factual source order for this capability is: executable source/tests at the exact subject → exact-head workflow evidence → Reference page → links from the other Diátaxis roles. Tutorial/how-to/explanation must not become parallel API specifications.

### Preserved v26.8.18 operational snapshot

The following pages describe the v26.8.18 release-era subject. They remain useful but are `HISTORICAL` with respect to capabilities merged later unless an individual page explicitly binds newer evidence:

- `docs/v26.8.18-release.md`
- `docs/ARCHITECTURE.md`
- `docs/OPERATIONS.md`
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
- release-era sections of `docs/SUMMARY.md` and `docs/00-introduction.md`
- `docs/jira/v26.8.18/00-OVERVIEW.md` through `04-GGEN-BRCE-CROSS-CUTTING.md`

`docs/README.md` and `docs/00-reading-map.md` are current routing documents and now state this boundary explicitly.

### Long-form doctrine/research corpus

`docs/01-*.md` through `docs/80-*.md` are authored `DOCTRINE` documents spanning constitution/type boundaries, semantic manufacture, closure/evidence, manufactured complexity/flow, authority/security/process, ecosystem realizations, post-AGI substrate independence, operating control, research, and TPS. Their architecture/mathematics may be current doctrine, but they are not evidence that a runtime edge executed.

### Nested handbooks and authored books

- `docs/post-agi-platform-handbook/**` — DOCTRINE; nested `SUMMARY.md` owns its exhaustive reading order.
- `docs/post-agi-marketplace-handbook/**` — DOCTRINE unless a page explicitly binds execution evidence.
- `docs/platform-engineers-handbook-*.md` — DOCTRINE/LOCAL bridge material.
- `docs/how-to-build-a-dyson-sphere/**` — authored book/speculative systems material; not operational evidence for repository capabilities.

### Historical audits

`docs/audits/**` and dated/gap-review evidence are `HISTORICAL`. Preserve the observed subject and append later closure pointers rather than rewriting the original observation.

### Future proof corpus

`docs/v26.9.1/**` is `FUTURE` unless a document explicitly supplies exact current-runtime evidence. `docs/v26.9.1/00_CANONICAL_INDEX.md` owns that frozen corpus. Specification freeze is not release `ALIVE`.

### Platform-console local documentation

`platform-console/README.md` and `platform-console/docs/**` are `LOCAL` to the deployable console, including data residency, DR/second-cluster, incident communications, scope/limitations, SOC2 mapping, and support/escalation. Cross-cutting docs should link instead of duplicating their contracts.

### Generated documentation/projections

The following are `GENERATED` and must not be manually corrected:

- `views/generated/*.md`
- `status/README.md`
- `status/repos/*.md`
- generated `soc2/*.md`
- generated status deck/output artifacts where applicable

Repair canonical inputs/generators and regenerate.

### Publication and registry surfaces

- `book.toml` defines `docs` as mdBook source; it is authored configuration.
- `docs/SUMMARY.md` is the authored publication graph. Its release-era `Current v26.8.18 Operations` heading is a historical navigation label, not a claim that no later capability exists. Current routing begins at `docs/README.md`/this inventory.
- `catalog/documents.toml` is the explicit cross-cutting document registry, not an exhaustive chapter index. Add entries only for documents that become control-plane constitutional/operational/release contracts.

## Replicated-evidence observed capability ledger

Observed in source at `main@be27c936...` and its merged PR #133 lineage:

- exact action admission precedes qualification; `DO` is `REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]`;
- lease validity is timezone-aware and half-open; stale admission is refused;
- empty/mixed subjects are refused; highest-generation disagreement becomes `SPLIT_BRAIN` and engine result `UNKNOWN`;
- strict majority is `n // 2 + 1`; insufficient quorum remains `UNKNOWN`;
- positive qualification is capped at `PARTIAL_ALIVE` with a receipt and `actuation_performed=False`;
- vector clocks preserve `EQUAL|BEFORE|AFTER|CONCURRENT` plus component-wise join;
- Merkle reduction is deterministic over sorted digests;
- receipt replay requires no actuation and exact digest equality;
- exact-head PR workflow compiles the package/tests, runs the permanent unittest court, and rejects common ambient actuation-capable imports.

Exact-head execution evidence: PR #133 head `7ce703f477eeb135f675156d71644a33ac532c1d`, workflow run `32608335688`, `DEVELOP Replicated Evidence Exact Head`, conclusion `success`. The merged repository subject reviewed here is `be27c93621ef494ccc342e0dc36c99dab9e391a6`; this documentation does not infer a new repository-wide Crown from that subsystem court.

## Archive decisions

No files were deleted. The v26.8.18 material has lineage and evidentiary value, so it is preserved in place and reclassified as a bounded historical release snapshot for post-baseline currentness. This avoids erasing evidence while removing its former role as the complete current capability map.

## Generated-document status

No generated documentation is edited by this transition. New/changed docs are authored surfaces. If a later generator claims ownership of any of these paths, canonical ownership must be changed before regeneration.

## Completeness falsifiers

This inventory becomes stale if any of the following occurs:

1. a new operator-visible capability ships without an owning current Tutorial/How-to/Reference/Explanation mapping or explicit coverage declaration;
2. a current page points at a superseded exact subject without stating the boundary;
3. a historical audit/release snapshot is rewritten as current evidence;
4. generated Markdown is hand-edited instead of regenerated;
5. future doctrine is relabeled as current runtime evidence;
6. a factual capability contract is duplicated across Diátaxis roles and drifts;
7. `ALIVE` is asserted from inspection, prose, test names, workflow presence, or stale CI instead of observed exact-subject execution.
