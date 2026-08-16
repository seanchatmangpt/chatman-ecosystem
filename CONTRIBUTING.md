# Contributing

This repository is governed by [`AGENTS.md`](AGENTS.md) (agent operating law and
release doctrine) and [`CONSTITUTION.md`](CONSTITUTION.md) (authority and receipts
model). Read both before making a change; this file only points at the entry
points and does not restate their content.

## Before you change anything

- Read [`AGENTS.md`](AGENTS.md) for the operating rules — what to preserve, how
  releases are graded, and the standing model.
- Read [`CONSTITUTION.md`](CONSTITUTION.md) for the authority and receipts model
  that changes must remain consistent with.
- Start from [`docs/README.md`](docs/README.md) for the long-form constitutional
  thesis and architecture/operations references.

## Making changes

- Prefer fixing forward: do not rewrite git history or delete commits.
  `git revert` is the one allowed history-changing operation.
- Never weaken, delete, or skip a negative fixture to obtain a green result
  (AGENTS.md rule 8).
- Treat generated files as projections; modify the canonical TOML or source
  instead (AGENTS.md rule 6).

## Verifying changes

- Run the narrowest relevant test while iterating, for example:
  - `python3 -m unittest discover -s tests -p 'test_*.py'` for the Python tooling
  - `cargo test -p <crate>` for a specific Rust crate
- Before advancing Crown standing, run the full admission gate:

  ```sh
  ./scripts/crown.sh
  ```

  This requires `cargo-deny`, `cargo-machete`, `curl`, `jq`, and `sha256sum` on
  `PATH`; it runs formatting, lint, test, doc, dependency-policy, catalog,
  receipt, projection, architecture, storage, and cold-cache gates, then
  produces and verifies a signed build manifest.
- The `Makefile` also exposes narrower targets: `make test`, `make verify`,
  `make survey`, `make audit-stubs`, and `make crown`.

## Opening a change

State what you changed and why, and which of the commands above you ran and
what they reported. A change without a corresponding real test run is not
verified — do not claim a gate passed unless you ran it.
