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
