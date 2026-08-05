# Architecture

## Dependency direction

```text
ecosystem-core
      ↑
ecosystem-runtime
      ↑
ecosystem-cli
```

`ecosystem-core` is intentionally free of Tokio, SQLx, Axum, Tower, Reqwest, and MCP framework dependencies. The architecture gate reads Cargo manifests and rejects those dependencies in the constitutional crate.

## Constitutional core

The core owns:

- Stable typed identities
- Exact subjects
- Standing transitions
- Exact authority classes
- Canonical catalog loading and validation
- BLAKE3 receipt sealing and verification
- Deterministic Markdown projections
- Crown evaluation

## Runtime adapters

The runtime crate owns replaceable implementations:

- Deterministic in-memory state storage
- SQLx-backed SQLite state storage
- Differential adapter verification
- Bounded governor execution with idempotency and timeout ambiguity
- MCP JSON-RPC boundary with broker refusal for direct mutation
- GitHub observation normalization
- Document revision normalization

## Authority boundary

Authority is exact, not ordinal. `Release` does not imply `Merge`; `Merge` does not imply `Communicate`; repository administration does not imply any control-plane authority.

## Receipt boundary

A receipt distinguishes observations, commands executed, artifacts changed, verifications performed, and exclusions. Blank source receipt digests are deterministically sealed into `target/crown/receipts`; the sealed copy is verified before Crown calculation.

## MCP boundary

The admitted v0.1 MCP surface is a bounded JSON-RPC server subset:

- `initialize`
- `tools/list`
- `tools/call`

Read-only Crown inspection is admitted. Mutations are refused at the MCP handler and must be submitted through the authority broker.

## Connectors

The v0.1 connector rail admits deterministic normalization and refusal contracts. GitHub live-read admission is performed by CI against the exact workflow SHA. External mutation remains outside the v0.1 authority grant.
