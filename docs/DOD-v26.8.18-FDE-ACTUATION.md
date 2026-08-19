# Definition of Done — v26.8.18: gymact + autofde-lab Actuation of platform-console

This document separates two things that are easy to blur in a milestone target: what "gymact and
autofde-lab can actuate platform-console like a Fortune-5 Forward Deployed Engineer" concretely
means for **this milestone** (a scoped, falsifiable target) versus what it does not claim (open-ended
autonomous production control). Every criterion below states a real, checkable condition, grounded in
file:line citations from three surveys run this session (gymact, autofde-lab, platform-console) — not
an adjective, and not aspirational language.

## 1. Scope — what "actuate like an FDE" means for v26.8.18

An FDE operating platform-console does a bounded set of things repeatedly: provisions/deprovisions
projects, runs the Castle deploy/run/sunset lifecycle, schedules and executes remediation jobs, and
diagnoses incidents via audit/cost/OCEL evidence. This milestone scopes "actuate" to the operations
that are **already real, authenticated HTTP surfaces on platform-console today** (per the
platform-console survey), because an actuator needs a real credentialed contract to call — building a
planner or adapter against a surface that doesn't exist yet is out of order.

**In scope for v26.8.18** (real routes, Bearer-API-key-authenticated, `requireSession`/`requireRole`
gated per `app/middleware.ts` + `app/lib/api-keys.ts`):

- Project provisioning/deprovisioning — `app/app/api/projects/route.ts`, `projects/[name]/*`.
- Castle lifecycle — `app/app/api/castle/{deploy,run,sunset}/route.ts`, `castle/route.ts`.
- Scheduled remediation jobs — `app/app/api/scheduled-jobs/route.ts` (POST, `commandId` resolved
  against a fixed server-side `ALLOWED_COMMANDS` allowlist — no raw command text accepted).
- DB migrations — `app/app/api/projects/[name]/migrations/route.ts` (apply/rollback, confirm-text
  guard).
- DB backup/restore — `app/app/api/projects/[name]/backups/route.ts`.
- Incident/audit evidence read — `app/app/api/audit/verify/route.ts` (hash-chain verification) and
  `app/app/api/ocel-log/route.ts` (proxies an OCEL accumulator's `/status`/`/discovery`).

**Explicitly OUT of scope for v26.8.18** (named, not omitted):

- `services/ggen/app.py`'s `/provision` endpoint. Per the platform-console survey, this is a bare
  stdlib HTTP server with **no application-layer credential** — no API-key or session gate observed
  in `app.py`'s handler. Actuating it today would rely on network policy alone, not a credential the
  console issued, which does not meet this milestone's authority-gating bar (§2, criterion 1). It is
  deferred until it either grows an equivalent Bearer-key gate or is retired in favor of the
  console's own provisioning route.
- Cost dashboard actuation/read (`app/app/cost/page.tsx`) — survey found no matching
  `app/app/api/cost` route; UNVERIFIED whether a JSON API backs it. Not actionable until confirmed.
- Tracing (`app/app/tracing/page.tsx`) — same reason: no `app/app/api/tracing` route found.
- Logs/log-search (`app/app/api/logs`, `app/app/api/log-search`) — directories exist, contents unread
  this session; contract UNKNOWN. Deferred until the contract is actually read and confirmed.
- Any k8s manifest beyond what `kubernetes_reconciliation.py` already covers (one fixed Pod,
  `scale_restart`/`get_status`) — a general "apply arbitrary platform-console manifest" adapter does
  not exist and is not built as part of this milestone (see gap in §3, criterion 1).
- Any RDF/PDDL-planned remediation sequence over platform-console concepts (services, deployments,
  health checks, quota limits) — no such domain model exists in autofde-lab's ontology catalog (§3,
  criterion 3), and authoring one from scratch is out of scope here.
- Full autonomous production control with no human oversight — see §5 (non-goals).

## 2. Falsifiable DoD criteria

Each criterion is a real, checkable condition — modeled on VISION.md's 2030-horizon bullet format: a
concrete thing that must exist, in a specific file, passing a specific test.

1. **A real gymact adapter exists that authenticates to platform-console with a service-account
   Bearer key, not a human session cookie, and every call passes through `AuthorityResolver` +
   `CapabilityScope` before it reaches the HTTP layer.** Concretely: a new provider module (e.g.
   `platform_console_provider.py`) implementing the `EnvironmentProvider`/`Environment` Protocol
   (`providers.py:13-38`) that either (a) reuses `HTTPJSONEnvironment`/`HTTPJSONProvider`
   (`network_providers.py:41-166`) if platform-console is fronted with the required
   `{GET /state, POST /act, POST /restore, GET /health}` contract, or (b) is a new direct-HTTP
   provider issuing real `Authorization: Bearer pk_live_...` requests to the in-scope routes listed
   in §1. The credential must be a key minted via `POST /api/api-keys` (owner-role only,
   `app/app/api/api-keys/route.ts`) and stored/read the way `GymAct.act()`'s existing
   `AuthorityResolver` (`kernel.py:739-762`) and `CapabilityScope` (`kernel.py:679-703`) gates expect
   — no adapter constructs its own bypass of those gates.
2. **A real receipted evidence record is produced per actuation, checkable against
   platform-console's own audit trail.** The adapter's `verify()` step polls the real Castle
   lifecycle status or project state (not just the HTTP 2xx), and the resulting `GymActResult`'s
   receipt is cross-checkable against `GET /api/audit/verify`'s hash-chain output for the same
   action — i.e., the audit log entry that `writeAuditLogEntry` unconditionally writes on every
   mutating route (per the platform-console survey) must match the gymact-side receipt for the same
   operation, by timestamp/action/actor correlation.
3. **At least one end-to-end round trip is demonstrated and reproducible**: a real gymact `act()`
   call against a real (non-production, test-tenant) platform-console deployment — e.g. `POST
   /api/projects` to provision a project, or `POST /api/castle/deploy` — followed by a real `verify()`
   poll of the resulting state via the console's own read routes, followed by a real audit-log
   cross-check per criterion 2. Run output (not a description) is the evidence: the actual HTTP
   status codes, the actual returned JSON, the actual `GymActResult`.
4. **The fail-closed conformance-checker path is exercised, not bypassed.** When routed via
   `mcp_process_control.dispatch`, the post-hoc `ConformanceChecker` replay (`mcp_process_control.py:
   93-138`) runs against the real captured actuation and either confirms or refuses it — with at
   least one test asserting a refusal on a real malformed/out-of-scope action (e.g. a `commandId` not
   in `ALLOWED_COMMANDS`, or an expired credential), proving the gate is load-bearing and not
   decorative.
5. **No scheduling/remediation-sequence claim is made without a domain model that actually encodes
   platform-console concepts.** If any milestone deliverable claims to "plan" a remediation sequence
   (as opposed to a single actuation), it must cite a real, tested domain file — analogous to
   `rdf_domain.py`'s `blocks_rdf_domain.ttl` fixture — that encodes at least one real
   platform-console concept (a service, a deployment, a health check) as a typed predicate, with a
   real Astar-or-equivalent solve producing a real plan, not a hand-written script framed as a plan.

## 3. Current gap per criterion (cited)

1. **No such adapter exists today.** gymact's registered providers (`registry.py:48-73`) cover
   local subprocess/CLI (`discovered.py`), filesystem/git/sqlite (`local_providers.py`), local Docker
   via Terraform (`terraform_docker_apply.py:1-40`), a narrow local-k8s reconciliation gym
   (`kubernetes_reconciliation.py:1-26`, hardwired to one fixed Pod manifest and two capabilities),
   and a generic HTTP-JSON contract (`network_providers.py:41-166`) — but nothing targets
   platform-console's actual `/api/*` routes or its Bearer-key auth scheme. The HTTP-JSON path is the
   closest fit but requires platform-console to expose the exact `{operation, payload}` action shape
   the provider expects, which it does not today (its routes are individually shaped, e.g.
   `POST /api/castle/deploy` with its own body schema, not a generic `/act` dispatcher).
2. **No cross-check exists.** Nothing in the gymact or autofde-lab surveys shows a receipt format
   that maps onto platform-console's audit hash-chain (`app/app/api/audit/verify/route.ts`). This is
   a new integration, not an extension of an existing one.
3. **No round trip has been run.** Neither survey reports an actual HTTP call from gymact/autofde-lab
   into platform-console — every gymact actuation surveyed targets local subprocess, local Docker, or
   local k8s, never a remote authenticated Next.js API.
4. **The gate itself is real and already load-bearing for other targets** (`mcp_process_control.py:
   93-138`), but has never been exercised against a platform-console-shaped action, so its
   refusal behavior in that context is unverified.
5. **No domain model exists.** autofde-lab's `rdf_domain.py` (383 lines, staged uncommitted, 5/5
   tests passing this session) compiles RDF Turtle into classical STRIPS PDDL, but its own docstring
   (`rdf_domain.py:5-24`) and the ontology header (`ontology/rdf-planning-domain.ttl:10`) state it
   "performs no admission, no receipt, no actuation" and the only proven fixture is single-block
   blocks-world (`tests/fabric/fixtures/blocks_rdf_domain.ttl`). RCPSP
   (`do_solver_scheduling.py:49-90`) is a mature, registered resource-allocation domain conceptually
   closest to scheduling under capacity constraints, but it is a disjoint pipeline from the RDF/PDDL
   path with no bridge, and neither encodes platform-console concepts (services, deployments, health
   checks, rollback windows, quota limits) — per the autofde-lab survey, "someone would have to
   author that domain from scratch."

## 4. Recommended first real increment

**Build one gymact `EnvironmentProvider` that actuates exactly one in-scope route —
`POST /api/projects` (provision) plus its `GET /api/projects/[name]` read for `verify()` — using a
real Bearer API key minted against a real (test-tenant) platform-console deployment, gated by the
existing `AuthorityResolver`/`CapabilityScope`, with a Chicago-style test that makes the real HTTP
call and asserts on the real returned JSON and status code (skip named + skipped, not mocked, when
no test-tenant deployment is reachable).**

Concrete scope for a build agent, in one pass:

- New file: `gymact/providers/platform_console_provider.py` (or the project's existing provider
  directory convention — confirm via `registry.py:48-73`'s pattern) implementing the `Environment`
  Protocol (`providers.py:13-38`) with two capabilities: `provision_project` (POST) and
  `get_project_status` (GET, used by `verify()`).
- Credential handling: read the Bearer key from an env var (e.g. `PLATFORM_CONSOLE_API_KEY`), never
  hardcoded, never logged in plaintext in the receipt.
- Register the provider in `registry.py` following the existing pattern used for
  `kubernetes_reconciliation.py` or `network_providers.py`.
- `verify()` must poll `GET /api/projects/[name]` and assert the real returned status field
  (not just the POST's 2xx), mirroring how `kubernetes_reconciliation.py:116+` polls real Pod phase
  rather than trusting apply exit code.
- Test file: real HTTP calls against a real reachable test-tenant platform-console instance (URL from
  env var), `pytest.mark.skipif` when unreachable — no `unittest.mock`/`monkeypatch` of the HTTP
  layer. Assert on the real returned project name/status/JSON shape, and on the real
  `GymActResult.exit_code`/receipt fields — not on "was `requests.post` called."
- Do not attempt criterion 2 (audit cross-check) or criterion 5 (planning) in this increment — those
  are separate, later increments once this narrowest round trip (criterion 3, provisioning only) is
  proven.

## 5. Non-goals

This DoD does not claim, and no future work under this milestone number should claim:

- **Full autonomous production control with no human oversight.** Every actuation described above is
  a single, individually-authorized API call using a credential a human owner explicitly minted
  (`POST /api/api-keys`, owner-role only) — not a standing grant of unattended control.
- **A general "apply any k8s manifest to platform-console" adapter.** Out of scope per §1; the only
  k8s-adjacent capability that exists today (`kubernetes_reconciliation.py`) is narrower than this
  milestone even attempts to extend.
- **A general "plan any remediation sequence" capability.** Per §3 criterion 5, no domain model
  exists; any planning claim without a cited, tested domain file encoding real platform-console
  concepts is out of bounds for this milestone.
- **Actuating `services/ggen/app.py`'s `/provision`.** Deferred until it has an application-layer
  credential gate equivalent to the console's Bearer-key scheme (§1).

**SELECT != DO / CONSTRUCT != DO, unrelaxed.** Every actuation described in this document is a DO
step that must be preceded by an authority-checked SELECT — `AuthorityResolver` and `CapabilityScope`
(`kernel.py:679-762`) gating every `GymAct.act()` call, and (where routed through MCP) the post-hoc
`ConformanceChecker` replay (`mcp_process_control.py:93-138`) auditing it afterward. No criterion in
§2 is satisfied by an adapter that calls platform-console's API directly, bypassing these gates — a
provider that skips `AuthorityResolver`/`CapabilityScope` does not count as meeting this DoD even if
the HTTP call itself succeeds. This mirrors CASTLE's own invariant (`VISION.md`): the admission chain
is inherited by every new adapter, never relaxed for one.
