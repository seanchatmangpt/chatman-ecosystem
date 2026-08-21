# XaaS-Core: ERRC Innovation Grid + Full TOGAF Scoping

**Status**: real, grounded in a 6-agent `ultracode` Workflow run (task `wnk0fyzvw`, run
`wf_6276f516-78d`, 2026-08-20). Four repos surveyed read-only (`~/chatmangpt`, `~/cns`,
`~/chatman-ecosystem`, `~/autofde-lab`), zero trust extended to those repos' own README/CLAUDE.md
claims per this session's standing discipline — every claim below is cited to a real file the
survey agent actually opened, or marked `UNVERIFIED`/absent.

Full per-repo survey transcripts: `/private/tmp/claude-501/.../scratchpad/wf_{4,5,6,7}_*.txt`
(chatmangpt, chatman-ecosystem, cns, autofde-lab respectively) — condensed below.

## 1. Per-Repo Ground Truth (condensed)

### `~/chatmangpt`
17+ submodule monorepo. Real: `speckit-ralph` gate/receipt Rust CLI (blake3-hashed JSON
envelopes, `failure_class` enum) — now under `.archive/retired/`. Its own audit doc
(`PORTFOLIO_REALITY.md`) names 3 unreconciled `mcpp` runtimes (`mcp-plus/`, `mcpp-a2a/`,
`sr-mcp/`, still un-archived), 18 branches with collided commit subjects, and an explicitly
unbuilt "selection function" (`MuStar`). `.claude/RALPH_LOOP_FINAL_SUMMARY.md`'s "7/7 100%"
claim is self-contradicted by `.claude/FINAL_IMPLEMENTATION_SUMMARY.md` in the same tree (158
compile errors, 45/7306 test failures). **No file references `ce:Capability` or
`platform-console-capabilities.ttl`** — zero existing cross-repo bridge.

### `~/cns`
Ontology→codegen precedent (`bitstar/generated/*.py` from `bitstar/cli_ontology.yaml`), real
`ThroughputMeasurement`/percentile-latency benchmark harnesses. Headline claims
("97.66 BILLION ops/sec") are directly contradicted by the repo's own validation report
(`HIVE_MIND_VALIDATION_REPORT.md`: "mocked"), a real run at 89.55 ops/sec
(`BENCHMARK_RESULTS_SUMMARY.md`), and a failed `MODULE_NOT_FOUND` target run — every performance
badge checked traces to a mocked or failed/unrelated test.

### `~/chatman-ecosystem`
`ontology/platform-console-capabilities.ttl`: 44 individuals, **100% `ce:capabilityClass ce:Do`**
(0 of any other class, despite importing a richer TBox at ttl:9), all `ce:standing "active"`, 9
`ce:reversible false`. Real end-to-end pattern: `lib/castle.ts` (allowlisted CLI-as-k8s-Job) →
`lib/approval-workflow.ts` (ConfigMap-backed maker-checker) → `lib/audit-db.ts` (durable Postgres
audit row) — the only fully governed, DB-backed capability-invocation chain found across all 4
repos.

### `~/autofde-lab`
Fork of Airbus scikit-decide + a real hand-built `receipts/` package (2861 lines): `Broker`
enforces actuator/verifier separation (`broker.py:65-68`) so no actuator self-certifies;
`level4_ocel.py` builds real OCEL event/object graphs from a sqlite3 receipt ledger; the LLM-agent
test suite named-skips against a real local model server rather than mocking
(`test_self_play_dspy_turbofieldfare_chicago.py`, confirmed by running it). 4 stale
`.claude/worktrees/agent-*` dirs and `TEMP_RLlib/`, `TEMP_CGP/`, `.ggen-v2.broken-2026-08-10/`
scratch dumps are dead weight, not source material.

## 2. ERRC Grid — xaas-core

### Eliminate
- 3 unreconciled `mcpp` runtimes + 5 doc trees — pick one canonical impl before porting gate
  logic. *chatmangpt, `PORTFOLIO_REALITY.md:134-140`.*
- Billion/million-ops headline claims — the repo's own validation report calls them mocked; real
  measured number is 89.55 ops/sec. *cns, `HIVE_MIND_VALIDATION_REPORT.md:33` vs
  `BENCHMARK_RESULTS_SUMMARY.md:11-13`.*
- BitFlow/BitActor benchmark harnesses that fail `MODULE_NOT_FOUND` — don't carry forward as
  capability-SLA evidence generators. *cns, `unified-benchmark-report.json`.*
- 18 collided-commit-subject branches — dead history, not a pattern source. *chatmangpt,
  `PORTFOLIO_REALITY.md:134-140`.*
- 4 stale `.claude/worktrees/agent-*` duplicate trees — purge before using autofde-lab as a
  capability-catalog source. *autofde-lab.*
- `TEMP_RLlib/`, `TEMP_CGP/`, `.ggen-v2.broken-2026-08-10/` scratch dumps — exclude from any
  xaas-core codegen source scan. *autofde-lab.*

### Reduce
- Collapse `castle.ts`'s CLI-as-Job wrapper to only verbs that actually exist server-side
  (`fortune5`, `inventory-*`) — its own header already documents `construct`/`gymact` as unbuilt.
  *chatman-ecosystem, `lib/castle.ts:1-19`.*
- Treat `PORTFOLIO_REALITY.md`'s described (not opened) config-precedence chain as
  reference-only until independently confirmed. *chatmangpt, `PORTFOLIO_REALITY.md:57`.*
- Spot-check depth, not full review, for bulk-generated capability-addition commits (`03df876`,
  `64b4e47`, `d6521de`) — git log shows no dedicated review commits for the files those PRs touch.
  *chatman-ecosystem.*
- Scope `fabric/ontology.py`/`shacl_conformance.py` (778 combined lines) to file-existence-only
  until contents are read — don't build xaas-core's SHACL layer on unverified fit. *autofde-lab.*

### Raise
- Promote the `ce:Do` → `requireApproval()` → k8s Job → `audit-db.ts` chain to the standard
  xaas-core capability-invocation pipeline — the only end-to-end governed pattern found.
  *chatman-ecosystem, ttl + `lib/approval-workflow.ts` + `lib/audit-db.ts`.*
- Make actuator/verifier separation (distinct Protocols, no self-certification) a required
  design constraint for every irreversible capability (9/44 are `ce:reversible false`).
  *autofde-lab, `receipts/broker.py:65-68,107-179`; chatman-ecosystem ttl reversibility flags.*
- Make the receipt-ledger → OCEL graph builder the standard audit/provenance backend, replacing
  the ephemeral stdout logger that still coexists with the DB-backed one. *autofde-lab,
  `level4_ocel.py:262-322`; chatman-ecosystem `lib/audit-log.ts` vs `lib/audit-db.ts`.*
- Make "real-server-or-named-skip" (never silent mock) the mandatory test pattern for any
  capability backed by an optional local service. *autofde-lab,
  `test_self_play_dspy_turbofieldfare_chicago.py:57,73,84`, confirmed by running it.*

### Create
- A cross-repo capability→pattern manifest mapping each of the 44 `ce:Capability` individuals to
  which repo's pattern (gate/receipt, broker, OCEL, CLI-as-Job) implements it — net new; no
  existing file references `ce:Capability` in any of the other 3 repos.
- A "MuStar" portfolio-level selection function choosing the canonical implementation per
  capability class — net new; chatmangpt's own audit names the gap, confirms it was never built.
  *`PORTFOLIO_REALITY.md:150-172`.*
- `ce:Select`/`ce:Construct`/`ce:Data`-class capabilities extending the ttl beyond its current
  100%-`ce:Do` coverage — net new; the imported richer TBox (`ontology/capabilities.ttl`) is
  otherwise unpopulated in this file.
- A TTL→ggen codegen bridge for `platform-console-capabilities.ttl` itself — net new; chatmangpt's
  and cns's own ontology→codegen pipelines only ever operate on their own ontologies.
- A unified benchmark/SLA harness combining cns's real throughput/latency dataclasses with
  autofde-lab's admission-gate refusal typing — net new composition, no cross-reference found
  between the two repos as they stand.

## 3. TOGAF Scoping — 4 Architecture Layers (`skos:closeMatch` only, never `owl:equivalentClass`)

Namespace `togaf:` = `http://www.semanticweb.org/ontologies/2020/4/OntologyTOGAFContentMetamodel.owl#`
(real, fetched this session). New local namespace `xaas:` =
`https://seanchatmangpt.github.io/chatman-ecosystem/ontology/xaas-core#`.

### 3.1 Business Architecture — the 4 Ash domains

Each domain groups governed actions serving one business function, so it fits
`togaf:BusinessCapability` (ability the business has) *and* `togaf:BusinessArchitectureComponent`
(structural realizer of its member `ce:Capability` individuals):

```turtle
xaas:XaasOperations a togaf:BusinessCapability, togaf:BusinessArchitectureComponent ;
    dcterms:title "Xaas.Operations" ;
    dcterms:description "Cluster/workload actuation: castle-verb inventory/run, k8s Job dispatch." ;
    skos:closeMatch togaf:BusinessCapability, togaf:BusinessArchitectureComponent .

xaas:XaasBilling a togaf:BusinessCapability, togaf:BusinessArchitectureComponent ;
    dcterms:title "Xaas.Billing" ;
    dcterms:description "Metering, invoicing, vendor-offboarding financial attestation." ;
    skos:closeMatch togaf:BusinessCapability, togaf:BusinessArchitectureComponent .

xaas:XaasGovernance a togaf:BusinessCapability, togaf:BusinessArchitectureComponent ;
    dcterms:title "Xaas.Governance" ;
    dcterms:description "Maker-checker approval, legal-hold, geofence, data-destruction cert -- the irreversible/high-authority action set." ;
    skos:closeMatch togaf:BusinessCapability, togaf:BusinessArchitectureComponent .

xaas:XaasPlatform a togaf:BusinessCapability, togaf:BusinessArchitectureComponent ;
    dcterms:title "Xaas.Platform" ;
    dcterms:description "Console admin: audit-log/OCEL querying, feature flags, org lifecycle." ;
    skos:closeMatch togaf:BusinessCapability, togaf:BusinessArchitectureComponent .
```

Every `pcc:*` capability individual then gets one domain link, e.g.:

```turtle
pcc:CastleVerbInventoryComponents    skos:closeMatch xaas:XaasOperations .
pcc:CastleVerbInventoryGoals         skos:closeMatch xaas:XaasOperations .
pcc:ApprovalFreezeOverride           skos:closeMatch xaas:XaasGovernance .
pcc:DataDestructionCertificateIssue  skos:closeMatch xaas:XaasGovernance .
```

**Gap disclosed**: no `ce:ashDomain` predicate exists in the ttl today — the above is a proposal
to *add*, inferred from title semantics for the 44, not a fact already encoded. Only 4 individuals
are hand-verified against the real file in this pass; applying the pattern to the rest is
mechanical but not yet executed.

### 3.2 Data Architecture — `togaf:DataEntity`

Grounded in the real receipt/OCEL/audit pattern found across chatman-ecosystem + autofde-lab:

```turtle
xaas:ReceiptEntity a togaf:DataEntity ;
    dcterms:description "Single-use, hash-chained record of one capability actuation (open/close, token, actuator, verifier result). Modeled on autofde-lab receipts/broker.py, receipt_store.py." ;
    skos:closeMatch togaf:DataEntity .

xaas:OcelEventEntity a togaf:DataEntity ;
    dcterms:description "OCEL event/object graph derived from a receipt ledger. Modeled on autofde-lab level4_ocel.py and chatman-ecosystem lib/ocel-log.ts." ;
    skos:closeMatch togaf:DataEntity .

xaas:AuditLogEntity a togaf:DataEntity ;
    dcterms:description "Durable platform_console.audit_log Postgres row (lib/audit-db.ts), distinct from the ephemeral stdout logger." ;
    skos:closeMatch togaf:DataEntity .

xaas:ApprovalRecordEntity a togaf:DataEntity ;
    dcterms:description "k8s ConfigMap-backed approval-workflow.ts entry gating irreversible/high-authority capabilities." ;
    skos:closeMatch togaf:DataEntity .

xaas:InvoiceEntity a togaf:DataEntity ;
    dcterms:description "Xaas.Billing metering/invoice line-item record." ;
    skos:closeMatch togaf:DataEntity .

xaas:CapabilityStateFactEntity a togaf:DataEntity ;
    dcterms:description "Ground-fact bridge row from the capability-state-snapshot route (commit 3cc72a2) for TTL/planner validation against live cluster state." ;
    skos:closeMatch togaf:DataEntity .
```

### 3.3 Application Architecture — the 44 generated Ash resources

Each generated resource is both a `togaf:ApplicationArchitectureComponent` (the resource module)
and exposes a `togaf:InformationSystemService` (its route surface):

```turtle
xar:CastleVerbInventoryComponentsResource a togaf:ApplicationArchitectureComponent ;
    dcterms:title "Ash.XaasOperations.CastleVerbInventoryComponents" ;
    skos:closeMatch togaf:ApplicationArchitectureComponent ;
    xaas:realizes pcc:CastleVerbInventoryComponents .

xar:CastleVerbInventoryComponentsService a togaf:InformationSystemService ;
    dcterms:title "POST /api/castle/run (inventory-components)" ;
    skos:closeMatch togaf:InformationSystemService ;
    xaas:exposedBy xar:CastleVerbInventoryComponentsResource .

xar:ApprovalFreezeOverrideResource a togaf:ApplicationArchitectureComponent ;
    dcterms:title "Ash.XaasGovernance.ApprovalFreezeOverride" ;
    skos:closeMatch togaf:ApplicationArchitectureComponent ;
    xaas:realizes pcc:ApprovalFreezeOverride .

xar:DataDestructionCertificateIssueResource a togaf:ApplicationArchitectureComponent ;
    dcterms:title "Ash.XaasGovernance.DataDestructionCertificateIssue" ;
    skos:closeMatch togaf:ApplicationArchitectureComponent ;
    xaas:realizes pcc:DataDestructionCertificateIssue .

xar:DataDestructionCertificateIssueService a togaf:InformationSystemService ;
    dcterms:title "POST /api/owner/data-destruction" ;
    skos:closeMatch togaf:InformationSystemService ;
    xaas:exposedBy xar:DataDestructionCertificateIssueResource .
```

Remaining 40 follow `xar:<PascalCaseTitle>Resource a togaf:ApplicationArchitectureComponent` +
`xaas:realizes pcc:<Individual>`, mechanically generated from the ttl's existing `dcterms:title`
strings — **not yet executed for all 44**, only the 4 above are hand-verified.

### 3.4 Technology Architecture — ecosystem packages, logical/physical split

A package name is `togaf:LogicalTechnologyComponent` (provider-agnostic requirement); its
concrete deployed instance in this ecosystem is `togaf:PhysicalTechnologyComponent`:

```turtle
xaas:AshPostgresLogical a togaf:LogicalTechnologyComponent ;
    dcterms:title "ash_postgres" ; skos:closeMatch togaf:LogicalTechnologyComponent .
xaas:AshPostgresPhysical a togaf:PhysicalTechnologyComponent ;
    dcterms:title "platform_console Postgres (kind-platform-eng-colima cluster)" ;
    dcterms:description "Live Postgres backing platform_console.audit_log, per lib/audit-db.ts." ;
    skos:closeMatch togaf:PhysicalTechnologyComponent ;
    xaas:realizesLogical xaas:AshPostgresLogical .

xaas:AshObanLogical a togaf:LogicalTechnologyComponent ;
    dcterms:title "ash_oban" ; skos:closeMatch togaf:LogicalTechnologyComponent .
xaas:AshObanPhysical a togaf:PhysicalTechnologyComponent ;
    dcterms:title "k8s batch/v1 Job runner (castle.ts verb dispatch)" ;
    dcterms:description "Self-cleaning k8s Jobs realizing async/queued verb actuation, functionally analogous to Oban's job-queue role." ;
    skos:closeMatch togaf:PhysicalTechnologyComponent ;
    xaas:realizesLogical xaas:AshObanLogical .

xaas:AshAuthenticationLogical a togaf:LogicalTechnologyComponent ;
    dcterms:title "ash_authentication" ; skos:closeMatch togaf:LogicalTechnologyComponent .
xaas:AshAuthenticationPhysical a togaf:PhysicalTechnologyComponent ;
    dcterms:title "AuthorityObject.admits(...) authority check (approval-workflow.ts)" ;
    skos:closeMatch togaf:PhysicalTechnologyComponent ;
    xaas:realizesLogical xaas:AshAuthenticationLogical .

xaas:IstioGatewayPhysical a togaf:PhysicalTechnologyComponent ;
    dcterms:title "Istio Gateway (kind cluster ingress)" ; skos:closeMatch togaf:PhysicalTechnologyComponent .
xaas:SupabaseOperatorPhysical a togaf:PhysicalTechnologyComponent ;
    dcterms:title "Supabase-operator Project/SingleDatabase CRDs" ; skos:closeMatch togaf:PhysicalTechnologyComponent .
xaas:CastleCliPhysical a togaf:PhysicalTechnologyComponent ;
    dcterms:title "castle Rust CLI binary (batch/v1 Job image)" ; skos:closeMatch togaf:PhysicalTechnologyComponent .
```

## 4. Disclosed Gaps (not smoothed over)

- Domain-to-capability assignment (§3.1) and the 44 resource/service pairs (§3.3) are proposals to
  add, not facts already in the ttl — only 4 of 44 are hand-verified against real file content in
  this pass; the remaining 40 follow mechanically but were not generated in this turn.
- The existing `xar:RenderTarget`/`togaf:Capability` closeMatch already in
  `ggen-marketplace/packs/xaas-ash-core-pack/ontology.ttl` was not re-opened in this pass; §3's
  naming convention is assumed consistent with it, not independently re-confirmed here.
- `fabric/ontology.py`/`shacl_conformance.py` (autofde-lab, 778 combined lines) were not read
  beyond existence/line-count — their fit as an XaaS SHACL layer is UNVERIFIED.
- `evidence/control-evidence-bundle.json` (chatman-ecosystem README's "not simulated" claim) was
  not opened — UNVERIFIED.

## 5. Next Step (not yet executed)

Apply §3's Turtle to `ggen-marketplace/packs/xaas-ash-core-pack/ontology.ttl` for all 44
individuals (currently only 4 are hand-verified examples above), re-run `ggen graph validate`,
then run the CQ01-28 competency-question checks in `xaas-public-ontology-profile` against the
other already-fetched public ontologies (PROV-O, ODRL, DCAT, ORG, SOSA, QUDT, SPDX, P-PLAN, FnO).
