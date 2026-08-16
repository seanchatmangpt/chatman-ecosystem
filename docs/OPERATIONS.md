# Operations and Admission

## Local Crown sequence

`./scripts/crown.sh` requires `cargo-deny` and `cargo-machete`, then performs:

1. Formatting check
2. Clippy across all targets and features with warnings denied
3. Locked workspace tests
4. Locked Rustdoc with warnings denied
5. Dependency, license, and source policy
6. Unused-dependency detection
7. Catalog validation
8. Receipt sealing and verification
9. Projection drift check
10. Architecture check
11. Memory/SQLx differential storage verification
12. Exact-subject Crown verification

GitHub Actions repeats these gates from a clean checkout. The remote Crown job is the release-admission authority for a candidate commit.

## Governor model

Governors move through:

`Planned → Admitted → Running → Succeeded`

Alternative states are `AwaitingInput`, `AwaitingAuthority`, `Failed`, `Ambiguous`, `Refused`, and `Superseded`.

Timeout is `Ambiguous`, not automatically retryable. Duplicate idempotency keys replay the prior result without re-executing the operation.

## Cache policy

- Pull requests may restore trusted default-branch caches.
- Pull requests do not save shared caches.
- Default-branch runs are the only shared cache writers.
- Keys derive from the runner platform and committed `Cargo.lock`.
- A cold-cache job deletes `target/` and proves correctness without cache.
- Cache contents are acceleration and never contribute standing.

## Artifact transfer

The test job builds one release binary for the exact candidate SHA and stages:

- The binary
- A build manifest
- The sealed receipt set

The manifest records source SHA, toolchain, target, lockfile digest, and binary digest. The final Crown job downloads the artifact, verifies the candidate SHA, lockfile digest, binary digest, and receipt presence, then calculates Crown standing.

## Release

The v0.1 release-admission rail creates and verifies a release-candidate workflow artifact. It does not publish a GitHub Release, package, container, or deployment. Publication remains a separate explicitly authorized operation.

## GitHub connector

CI performs a live, read-only GitHub API smoke test using the repository-scoped token. It confirms repository identity and the exact candidate commit. No comments, labels, merges, branch mutations, releases, or other remote mutations occur.

## Document connector

The v0.1 document connector admits deterministic normalization of stable document identity, revision, canonical path, and BLAKE3 digest. Remote Google Drive reads and writes are outside this version's declared contract.

## MCP boundary

The v0.1 MCP rail is a bounded JSON-RPC surface for `initialize`, `tools/list`, and `tools/call`. Read-only Crown inspection is admitted. Direct mutation is refused and must be brokered under exact authority. This is not a claim of complete MCP protocol conformance.

## Gall checkpoints

The scheduled Gall workflow resolves and receipts the current default-branch SHA for each registered external candidate. `GALL_CHECKPOINTS = ALIVE` means the exact-subject observation mechanism works. It does not confer behavioral standing on any external repository.

## Schemas

Rust's typed TOML deserialization and explicit catalog validation are the executable v0.1 manifest checks. `schemas/receipt.schema.json` is the published interchange contract; it does not replace the Rust verifier or independently confer standing.
