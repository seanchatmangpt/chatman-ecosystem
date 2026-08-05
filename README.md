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
