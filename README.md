# Chatman Ecosystem

The constitutional control plane, project graph, documentation registry, automation policy layer, and evidence ledger for the Chatman Ecosystem.

## Core invariant

> Zero unreceipted actuation.

The broker is the only lawful `DO` path. Frameworks, connectors, MCP handlers, scheduled governors, and database adapters may submit intentions; none may confer standing or bypass authority.

## Workspace

- `ecosystem-core`: stable identity, exact subjects, standing, authority, catalogs, receipts, projections, Crown evaluation.
- `ecosystem-runtime`: memory and SQLx/SQLite adapters, governor execution, MCP boundary, GitHub/document normalization.
- `ecosystem-cli`: process-level operator interface.
- `catalog/`: canonical TOML source.
- `receipts/`: source receipts; blank digests are sealed into `target/crown/receipts` during verification.
- `views/generated/`: deterministic projections. Do not edit manually.

## Admission

```bash
./scripts/crown.sh
```

The command terminates successfully only when the required rails share one exact subject and evaluate to `ALIVE`.

## Useful commands

```bash
cargo run -p ecosystem-cli --bin ecosystem -- catalog validate
cargo run -p ecosystem-cli --bin ecosystem -- receipt verify-all
cargo run -p ecosystem-cli --bin ecosystem -- projection check
cargo run -p ecosystem-cli --bin ecosystem -- architecture check
cargo run -p ecosystem-cli --bin ecosystem -- storage verify
cargo run -p ecosystem-cli --bin ecosystem -- crown --verify
```

The generated standing matrix is in [`views/generated/standing.md`](views/generated/standing.md).
