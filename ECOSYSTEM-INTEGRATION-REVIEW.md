# Chatman Ecosystem Integration Review

Honest status of five repos and the integration work attempted against them this pass. Each
section: real purpose, real API surface, and what actually happened when integration was
attempted — built+verified, partially done, or infeasible, with the concrete reason.

## wasm4pm

**Real purpose**: evidence-oriented process-mining platform (Rust + WASM + TypeScript). The
`wpm` CLI discovers/validates process models, operates on XES and OCEL-v2 event data, executes
POWL routes, and manufactures blake3-hashed replayable evidence. Repo's own standing is
`PARTIAL_ALIVE`, not a finished product.

**Real API surface**: two distinct `wpm` binaries — a published TS CLI
(`apps/wasm4pm/src/cli.ts`, noun-verb: log/model/pipeline/evidence/config/system/lab/help) and a
smaller Rust dev CLI (`crates/wasm4pm-cli/src/main.rs`: Doctor/Wizard/Telco/Mining/Config/
Autoprocess/Agent/Spc/Audit). WASM exports: `load_ocel_v2`, `flatten_ocel_v2`,
`discover_powl_from_log[_config]`, `parse_powl`, `validate_partial_orders`, `powl_execute`.

**Integration attempted this pass**: none. No build task targeted wasm4pm in this review round —
only survey work was done. Existing real (pre-existing, not new) integrations are limited to
autofde-lab's `wasm4pm_bridge.py` (shells to the built `wpm` binary, skips cleanly if absent) and
`receipts/wasm4pm_cognition.py` (spawns a real `node` process against the built TS CLI). No
platform-console or castle wiring exists or was attempted.

## wasm4pm-compat

**Real purpose**: nightly-only Rust library for compile-time typed admission of process-mining
evidence (event logs, OCEL, XES, BPMN, POWL, etc.) into a witness-checked `Admitted` state. No
execution/discovery/replay — structure-only, phantom-typed `Evidence<T, State, W>` carrier,
named refusal enums, not string errors.

**Real API surface**: pure library, no CLI/service/WASM-ABI. Core: `Evidence<T, State, W>`
(`src/evidence.rs`), `Admit` trait (`src/admission.rs`), `Admission`/`Refusal` re-exports, 40+
`pub mod` surfaces for each formalism (ocel, xes, bpmn, petri, powl, declare, etc.). Three
Cargo features: `formats` (default), `strict`, `wasm4pm`.

**Integration attempted this pass**: none. No build task targeted this repo. Zero real
code-dependency edges exist today from wasm4pm-compat into platform-console, castle, or gymact —
all found references are documentation/status prose (`status/repos/wasm4pm-compat.md`,
`docs/51-ecosystem-map.md`) or ephemeral worktree artifacts, not committed dependencies.

## gymact

**Real purpose**: Python reference runtime for a bounded, fail-closed benchmark/gym execution
profile, composing PROV-O/P-PLAN/SOSA/WoT/ODRL/SHACL public vocabularies. Enforces that
request-acceptance, world-change, verification, and scoring are never collapsed into one claim.
~30+ real gym providers drive real external systems (e.g. real `kubectl` subprocess calls against
a real cluster). BLAKE3/RFC-8785 hash-chained receipts.

**Real API surface**: Typer CLI (`gymact {version,execute,verify,observe,reconcile,replay,
benchmark,serve,...}`), Python API (`GymAct` runtime, `MaterializationIntent`,
`ActuationIntent`), FastAPI/FastMCP/FastStream native surfaces. Live-confirmed provider list via
platform-console's `services/gymact/facts.json`.

**Integration attempted this pass — castle side: built and verified.** Added
`ProcessGymActAdapter` in `castle::castle.rs`, shelling to the real `gymact verify` CLI against
the live `kind-platform-eng-colima` cluster's `kubernetes-reconciliation` provider, gated by a
fixed construction-time allowlist (unlisted transitions refused before `gymact` runs). Routes
through the existing `execute_powl_with_gym_act` admission chain unmodified. Two new Chicago-style
tests added (`tests/castle.rs`); `cargo test --test castle` → 16/16 passing, confirmed live (not
recalled from memory). Post-test `kubectl get pods` confirmed no leaked pod (adapter's
best-effort teardown worked). `grep` for mock patterns → zero matches. Honest gap: only wired to
`gymact verify`, not the heavier `gymact execute` DO path (BRCEBroker/`ExecutionGrant`) — flagged
open in `VISION.md`. Adapter selection is not config/env-driven; callers construct it directly,
same as the pre-existing `KindClusterReadOnlyGymAct`. Files staged, not committed: `VISION.md`,
`src/castle.rs`, `tests/castle.rs` in `~/castle`.

**Integration attempted this pass — platform-console side: partially done, deploy step
infeasible.** Built and verified locally: ran gymact's real FastAPI kernel
(`gymact serve --host 127.0.0.1 --port 8815`) and exercised the full `/episodes`,
`/capabilities`, `/observations/latest`, `/verify`, `/checkpoint`, `/evidence` surface with real
curl output (real episode IDs, real receipts, evidence chain `verified:true`). Added
`app/lib/gymact-kernel.ts`, `app/app/api/gymact-kernel/route.ts`,
`app/components/KernelPanel.tsx`, and updated `k8s/services-and-deployments.yaml` /
`k8s/network-policies.yaml`. `npx tsc --noEmit` clean, `npm run build` succeeded with the new
route/page present in output. **What failed**: deploying the kernel into the live cluster.
`kubectl get svc,deploy -n gymact` confirmed only the pre-existing static `gymact-status` exporter
runs there — no live kernel Service existed before this work, and none exists after it. The
production image build failed for a real, identified reason: gymact's `powl` dependency pulls in
`rustxes` (pyo3/maturin) → `polars` → `ethnum 1.4.0`, which fails to compile against current
stable rustc on linux/arm64 (`error[E0512]: cannot transmute between types of different sizes`) —
an upstream crate/architecture incompatibility, not a gymact or platform-console bug. Fixing it
would mean pinning an older rustc or patching the `ethnum` dependency inside `powl`'s tree — out
of scope this pass. The Deployment manifest is staged but deliberately **not applied** (applying
it against no real image would only produce `ImagePullBackOff`). No evidence-bundle entry was
added, since that bar requires live in-cluster verification this pass didn't reach.

## autofde-lab

**Real purpose**: fork of Airbus's scikit-decide, repositioned as the ecosystem's non-actuating
planning/decision layer — "it computes candidate plans, it does not actuate." Actuation is
delegated to gymact via a real path dependency and entry-point registration
(`azuregoat_privesc` provider). Vendored gyms are read-only reference checkouts, never imported.

**Real API surface**: Python 3.10+ with a compiled C++20/pybind11 solver core. CLI/MCP surface:
`python -m autofde_lab.openclaw_bridge {inspect|call|mcp}`, a real stdin/stdout JSON-RPC MCP
server (`openclaw_bridge.py`). Dispatch backend `openclaw_runtime.py`: `catalog()`, `describe()`,
`execute(name, arguments)`. Declared entry-points: `autofde_lab.domains`, `autofde_lab.solvers`.

**Integration attempted this pass: built and verified live.** In autofde-lab: added
`src/autofde_lab/openclaw_http.py`, a stdlib HTTP wrapper around the real
`openclaw_bridge._mcp_response` dispatch (same dispatch the stdio MCP server uses — no
reimplementation). In platform-console: built `services/autofde-lab-mcp/` (Dockerfile, prep
scripts — real build backend needs a ~2.3GB `cpp/` CMake tree not present, so the image skips
wheel-building and derives entry-points mechanically from the real `pyproject.toml`'s 89 real
domain/solver entries), `app/lib/openclaw.ts` (fail-closed client), `app/app/api/openclaw-catalog/
route.ts` (session-gated), new `openclaw-tool` search category in global search, k8s Deployment/
Service/NetworkPolicy in the `autofde-lab` namespace, and a new evidence-bundle control entry with
a recomputed blake3 digest. **Live-verified**: image built via colima/kind, loaded into the real
`kind-platform-eng-colima` cluster, pod confirmed `Running`. Through the real cluster Service:
`/healthz` → `{"status":"ok"}`; `tools/list` → real 8-tool catalog; `tools/call(catalog)` → 31
real domains, 57 real solvers, `ok:true`. `npx tsc --noEmit` clean. `grep` for mock patterns →
zero matches (only pre-existing comments in copied source). **Disclosed limitation**: only the
read-only `catalog`/`describe`/`match` surface works in this sidecar — the advertised `run` tool
would fail at import time, since the domains/solvers extras (matplotlib, cartopy, ray,
unified-planning) were deliberately excluded from the minimal image. Files untracked in
autofde-lab, staged (not committed) in platform-console.

## mmdio

**Real purpose**: "Mermaid Markdown I/O" — parses Mermaid diagram text into typed Pydantic AST
models and renders back to Mermaid text, round-trippable, across 11 diagram types. Engine code is
generated from an RDF ontology via `ggen`, validated by 10 SPARQL law gates.

**Real API surface (before this pass)**: library-only in practice. CLI (`mmdio.cli`) exposed only
a placeholder `fire` command; FastAPI app (`api.py`) exposed only a placeholder `/compute`
Fibonacci endpoint. Real, working parts were the Python engine functions: `parse_mermaid()`,
`render_diagram()`, per-type parse/render functions, `diff()`/`merge()`/`validate_topology()`.

**Integration attempted this pass: built and verified live.** In mmdio: added
`mmdio render-flowchart --json <path>` — the first real CLI subcommand — which parses a node/edge
JSON schema through the real `FlowchartDiagram` Pydantic model and calls the real
`render_diagram()`. Live-verified: valid input produces real rendered Mermaid text; missing
required field raises a real Pydantic `ValidationError` (exit 1); malformed JSON raises a real
`JSONDecodeError` (exit 1). Needed `uv sync --extra all` to pull in `lark` (an optional extra, not
a base dependency). In platform-console: added `app/lib/mermaid.ts` (shells to `uv run mmdio
render-flowchart` via `spawnSync`, same subprocess+JSON bridge pattern as
`lib/container-exec.ts`), `app/lib/topology.ts` gained `buildFlowchartInput()` (re-projects the
existing `TopologySnapshot` — the same data the deck.gl/isoflow tabs already use — into mmdio's
node/edge shape), and a third "Mermaid (mmdio)" tab was added to `app/app/topology/page.tsx`
showing the real rendered text or an honest error `Alert` on failure. Live-verified: reproduced
the exact `spawnSync` call from Node against the real mmdio checkout, `status: 0`, real Mermaid
output for a 2-namespace/1-edge input. `npx tsc --noEmit` and `eslint` clean on all touched files
(one pre-existing, unrelated Playwright-fixture type error in `e2e/fixtures.ts` from an earlier
session, untouched here). Evidence-bundle digest method reproduced and verified against the
existing stored digest before appending a new control entry. **Not done**: no client-side
Mermaid.js rendering — the tab shows raw Mermaid source text, not a rendered SVG; adding a
rendering library was out of scope (asked for text generation via mmdio's renderer, not a
rendering UI).

## Summary table

| Repo | Attempted this pass | Outcome |
|---|---|---|
| wasm4pm | No | Not touched; pre-existing bridges in autofde-lab remain the only real integration |
| wasm4pm-compat | No | Not touched; zero real code-dependency edges found anywhere |
| gymact ↔ castle | Yes | Built + live-verified (16/16 tests passing, real cluster probe) |
| gymact ↔ platform-console | Yes | Local kernel exercised live; in-cluster deploy blocked by a real upstream `ethnum`/rustc build failure |
| autofde-lab ↔ platform-console | Yes | Built + live-verified in-cluster; `run` tool intentionally unsupported in this sidecar |
| mmdio ↔ platform-console | Yes | Built + live-verified; renders Mermaid text only, no SVG rendering added |
