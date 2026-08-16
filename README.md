# Chatman Ecosystem

The constitutional control plane, project graph, documentation registry, automation policy layer, and evidence ledger for the Chatman Ecosystem.

## Core invariant

> Zero unreceipted actuation.

The broker is the only lawful `DO` path. Frameworks, connectors, MCP handlers, scheduled governors, and database adapters may submit intentions; none may confer standing or bypass authority.

## Workspace

- `ecosystem-core`: stable identity, exact subjects, standing, authority, catalogs, receipts, projections, and Crown evaluation.
- `ecosystem-runtime`: memory and SQLx/SQLite adapters, governor execution, bounded MCP handling, and GitHub/document normalization.
- `ecosystem-cli`: fail-closed process interface used by operators and CI.
- `catalog/`: canonical TOML source.
- `receipts/`: source receipts; blank digests are sealed into `target/crown/receipts` during verification.
- `views/generated/`: deterministic projections. Do not edit manually.

## Admission

Install `cargo-deny` and `cargo-machete`, then run:

```bash
./scripts/crown.sh
```

The command terminates successfully only when the required rails share one exact Git subject, all canonical receipts verify, generated views have no drift, architecture and dependency policies pass, storage adapters agree, and every required rail evaluates to `ALIVE`.

GitHub Actions additionally verifies a clean cold-cache build, a live read-only GitHub observation, and an exact-SHA candidate artifact before the remote Crown job succeeds.

## Useful commands

```bash
cargo run --locked -p ecosystem-cli --bin ecosystem -- catalog validate
cargo run --locked -p ecosystem-cli --bin ecosystem -- receipt verify-all
cargo run --locked -p ecosystem-cli --bin ecosystem -- projection check
cargo run --locked -p ecosystem-cli --bin ecosystem -- architecture check
cargo run --locked -p ecosystem-cli --bin ecosystem -- storage verify
cargo run --locked -p ecosystem-cli --bin ecosystem -- crown --verify
```

## Declared v0.1 boundaries

- MCP: bounded JSON-RPC subset; not complete protocol conformance.
- GitHub: live read-only exact-head observation; no mutation authority.
- Documents: deterministic local identity/revision/digest normalization; no live Drive mutation.
- Gall: external exact-subject observation; no inherited behavioral standing.
- Release: verified workflow artifact; no publication or deployment.

See [`docs/OPERATIONS.md`](docs/OPERATIONS.md) for the exact admission contract and [`views/generated/standing.md`](views/generated/standing.md) for the generated rail matrix.

---

# Chatman Ecosystem GALL Capsule

This repository is the integration boundary for the first four Gall checkpoints
of the Rust agent fabric. It does **not** promote the aggregate standing of any
source repository. It admits exact source coordinates, extracts bounded
invariants, and executes one dependency-free Rust capsule.

## Authority

`chatman-ecosystem` is the only actuation authority in this graph.

| Source | Admitted role | Authority ceiling |
|---|---|---|
| TRUEX | receipt and replay invariant reference | no actuation |
| MCPP | component/capability boundary reference | no actuation |
| wasm4pm | process and WASM evidence reference | no actuation |
| Ferroplan | deterministic plan construction | no authorization |
| MFW | independent planning oracle | evidence only |
| ggen | deterministic manufacture | no standing |
| mfact | certification reference | no actuation |
| UNRDF | semantic admission reference | no actuation |
| chatman-ecosystem | exclusive BRCE owner | bounded DO |

Exact commits are pinned in [`ecosystem.lock`](ecosystem.lock).

## Executable Gall sequence

```text
GALL-S0 source admission
  -> GALL-S1 receipt-bearing BRCE
  -> GALL-S2 gateway, sessions and four channel adapters
  -> GALL-S3 capability-fenced WebAssembly skill
  -> GALL_CROWN
```

A later checkpoint is unreachable when an earlier checkpoint fails.

### S0 — Phase 0 ALIVE boundary

- Nine exact 40-character source identities.
- One and only one `actuation-authority`.
- Duplicate and multiple-authority graphs are refused.
- Source graph has a SHA-256 identity.

### S1 — Phase 1 ALIVE boundary

- Canonical action object.
- Exact action/policy admission token.
- One private actuation function behind BRCE.
- Success and refusal receipts in one hash chain.
- Receipt verification and deterministic replay.
- Post-admission mutation and undeclared capabilities are refused.

### S2 — Phase 2 ALIVE boundary

- CLI, WebChat, Telegram and Discord messages use one gateway core.
- External channel identities map to bounded internal subjects.
- Unknown and revoked subjects are refused and receipted.
- Message content cannot expand capability authority.

These are deterministic local channel adapters, not claims of live third-party
network connectivity.

### S3 — Phase 3 ALIVE boundary

- A real valid WebAssembly module is parsed and interpreted.
- Its immutable SHA-256 digest is bound by a capability manifest.
- Only `fabric.actuate` is imported.
- The import re-enters BRCE; the interpreter has no ambient host authority.
- Undeclared imports, module drift and fuel exhaustion are refused and receipted.

The interpreter is intentionally an MVP subset for one Gall skill shape. It is
not a general WebAssembly engine.

## Replay

```bash
cargo test --all-targets
cargo run --bin gall
cargo run --bin gall -- --json
```

The JSON command emits four `ALIVE` checkpoints and one crown receipt. CI saves
that output as the `gall-receipt` artifact.

## Claim ceiling

`ALIVE` applies only to the exact dependency-free capsule and its executed
fixtures at the published commit. It does not claim:

- aggregate MCPP readiness;
- aggregate wasm4pm readiness;
- live Telegram or Discord service connectivity;
- a general-purpose WebAssembly runtime;
- formal Lean correspondence;
- migration of an OpenClaw installation.

Those are subsequent Gall systems and remain fenced until this smaller system
works at the exact head.

---

## The operating system for forward deployment

The Chatman Ecosystem is a portfolio of applications, infrastructure, semantic systems, planning tools, verification systems, and agentic workflows built to make forward deployment repeatable.

A forward-deployed engineer enters an incomplete operational environment, discovers the actual workflow, integrates fragmented systems, builds the local solution, puts it into operation, verifies the consequence, and transfers reusable capability. The Chatman Ecosystem turns that practice into an explicit engineering system:

```text
parse
→ route
→ admit or refuse
→ diagnose or repair
→ construct
→ actuate
→ observe consequence
→ verify
→ receipt
→ replay or hook
→ standing
```

The governing formulation is:

```text
A = μ(O*)
R = receipt(A)
```

- `O` is partial, stale, ambiguous, or untrusted observation.
- `O*` is admitted observation: identified, aligned, grounded, bounded, and authority-checked.
- `μ` is lawful manufacture.
- `A` is the resulting artifact, action, or changed system state.
- `R` binds identity, authority, execution, consequence, verification, and replay.

The operating invariant is **zero unreceipted actuation**. Models, planners, generated code, semantic derivations, proofs, and hooks may construct candidates or intents; they do not receive ambient authority to change the world.

## The 2,001st Forward-Deployed Agentic Architect

Sean Chatman is publicly documenting the case for **The 2,001st Forward-Deployed Agentic Architect**: the next member of an estimated cohort of 2,000 unusually qualified forward-deployed engineers.

This is a public nomination backed by an open implementation portfolio—not a claim of formal certification or ordinal ranking.

July 2026 portfolio snapshot:

- **3,146 GitHub commits**
- **40 repositories changed**
- **19,500 GitHub contributions** over the preceding twelve months

The larger objective is not to remain one scarce FDE. It is to build the system that makes high-integrity forward deployment teachable, reproducible, verifiable, and scalable.

## Ecosystem correspondence

| Forward-deployment requirement | Ecosystem surface |
|---|---|
| Discover and bound the customer environment | admitted observation, `O*`, STAR-TOML, public ontologies |
| Model operating processes | PPDDL, POWL, OCEL, process intelligence |
| Select and plan lawful work | scikit-decide and formal planning surfaces |
| Manufacture applications and infrastructure | MU, ggen, full-stack applications, Terraform, CI/CD |
| Integrate agents and tools | CLI, MCP, A2A, DSPy, knowledge hooks |
| Control real-world effects | BRCE and explicit authority boundaries |
| Prove the realized consequence | receipts, BLAKE3 identity, OpenTelemetry, replay |
| Explore failure before production | ontology-driven self-play and negative fixtures |
| Reuse learning across deployments | canonical graphs, generated projections, semantic caching |

Individual repositories preserve their own purpose, license, provenance, and maturity status. Inclusion in this portfolio does not imply that every repository was authored from scratch, is production-ready, or has achieved full ecosystem integration.

## Portfolio standing

**PARTIAL_ALIVE**

The architecture and substantial component implementations exist. Individual repositories have distinct evidence ceilings. Full portfolio standing requires exact-head integration, observed execution, verified receipts, and replay across the admitted deployment subject.

---

The composition root for the Chatman Ecosystem release train.

This repository does **not** reimplement ggen, AutoFDE, GymAct, process intelligence, formal proof, or provenance. It binds their exact identities into a dependency-closed release subject and refuses to crown a different graph than the one admitted.

## v26.9.1

The first major release target is `26.9.1` on 2026-09-01.

```text
research / explore
  -> semantic admission
  -> deterministic manufacture
  -> formal admission
  -> bounded actuation
  -> process evidence
  -> provenance / replay
  -> Fortune-5 capstone
  -> ecosystem crown
```

The exact component graph is `release/v26.9.1/manifest.toml`. Every release-blocking repository is pinned by repository, branch ref, and 40-character commit SHA. A ref name is never accepted as an identity.

## Standing law

`UNKNOWN`, `PARTIAL_ALIVE`, `ALIVE`, `BLOCKED`, `BUILD_BROKEN`, and `UNSUPPORTED` are distinct. A pinned Git commit proves identity only. It does not prove execution, verification, receipt integrity, replay, or release standing.

The manifest intentionally begins at `UNKNOWN`. The crown becomes `ALIVE` only when every required component has separately earned `ALIVE` against its exact admitted subject.

## Verify

```bash
python3 scripts/verify_release.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Check public refs live and validate exact externally observed evidence for private release components:

```bash
python3 scripts/verify_release.py --check-refs
```

Private sibling repositories are never silently skipped: they must carry an authority-named exact observation in the release manifest because a repository-scoped GitHub Actions token cannot see them. The strict crown command still fails until the release is actually ALIVE:

```bash
python3 scripts/verify_release.py --check-refs --require-alive
```

## Zero ambient authority

This repository is SELECT/CONSTRUCT release control. It does not actuate infrastructure, merge pull requests, publish packages, or grant BRCE authority. Those consequences remain in their owning systems and require their own receipts.
