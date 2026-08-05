# Operations and Admission

## Local Crown sequence

`./scripts/crown.sh` performs:

1. Formatting check
2. Clippy across all targets and features
3. Workspace tests
4. Rustdoc with warnings denied
5. Catalog validation
6. Receipt sealing and verification
7. Projection drift check
8. Architecture check
9. Memory/SQLx differential storage verification
10. Crown verification

## Governor model

Governors move through:

`Planned → Admitted → Running → Succeeded`

Alternative states are `AwaitingInput`, `AwaitingAuthority`, `Failed`, `Ambiguous`, `Refused`, and `Superseded`.

Timeout is `Ambiguous`, not automatically retryable. Duplicate idempotency keys replay the prior result without re-executing the operation.

## Cache policy

- Pull requests may restore trusted default-branch caches.
- Pull requests do not save shared caches.
- Default-branch runs are the only shared cache writers.
- Keys derive from toolchain, target, and `Cargo.lock`.
- A cold-cache job proves correctness without cache.
- Cache inventory and timing are emitted as operational evidence, never as correctness proof.

## Artifact transfer

The build job emits an exact-SHA manifest with source SHA, toolchain, target, lockfile digest, and binary digest. Downstream admission validates the manifest before using the artifact.

## Release

The v0.1 release-admission rail creates a release candidate artifact containing source identity, checksums, generated views, schema, receipt templates, and Crown report. Publication remains a separate explicitly authorized operation.

## GitHub connector

CI performs a read-only GitHub API smoke test using the repository-scoped token. It confirms repository identity and current workflow SHA. No comments, labels, merges, branch mutations, or releases occur.

## Document connector

The v0.1 document connector admits canonical path, revision, and BLAKE3 digest normalization for registered documents. Remote Google Drive mutation is not part of this version's declared contract.
