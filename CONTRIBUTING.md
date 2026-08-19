# Contributing

This repository is governed by [`AGENTS.md`](AGENTS.md) and [`CONSTITUTION.md`](CONSTITUTION.md). Read both before making a cross-cutting change. This file routes contributors to the executable verification and documentation contracts; it does not override constitutional law.

## Orient first

- [`docs/README.md`](docs/README.md) — documentation landing page
- [`docs/DOCUMENTATION-INVENTORY.md`](docs/DOCUMENTATION-INVENTORY.md) — complete documentation map and lifecycle classes
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — current v26.8.18 architecture
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md) — current admission/operator model
- [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) — development and verifier commands
- [`docs/DOCS-MAINTENANCE.md`](docs/DOCS-MAINTENANCE.md) — documentation source-of-truth/generated-file rules
- [`docs/VERSIONING.md`](docs/VERSIONING.md) — current v26.8.18 versus future v26.9.1 subjects

## Before you change anything

1. resolve the exact base SHA;
2. inspect applicable canonical TOML/source and nested doctrine;
3. identify whether the file is canonical, current, historical, generated, future, or component-local;
4. preserve `UNKNOWN != ALIVE`, inspection != execution, and `SELECT != CONSTRUCT != DO`;
5. do not infer authority from credentials, repository ownership, connector access, or model output.

## Making changes

- Prefer forward, additive, reversible changes where possible.
- Do not rewrite published Git history to make evidence look cleaner.
- Never weaken/delete/skip a negative fixture merely to obtain green CI.
- Treat generated files as projections. Change canonical source/generator and regenerate.
- Keep framework dependencies out of the constitutional core when architecture gates forbid them.
- Preserve explicit refusal and failure semantics; do not replace a real unavailable dependency with a fake success path.

## Verification

Run the narrowest relevant verifier while iterating, then expand.

Examples:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
cargo test -p <crate>
```

Before advancing repository Crown standing, run:

```bash
./scripts/crown.sh
```

The integrated gate covers formatting/lint/tests/docs/dependency policy/catalog/receipts/projection drift/architecture/storage and exact-subject Crown behavior according to the current repository scripts.

The Makefile also exposes narrower targets such as `make test`, `make verify`, `make survey`, `make audit-stubs`, and `make crown` where available.

For subsystem-specific commands, see [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## Documentation changes

When adding or changing docs:

- update [`docs/DOCUMENTATION-INVENTORY.md`](docs/DOCUMENTATION-INVENTORY.md);
- update `docs/SUMMARY.md` for mdBook pages;
- register cross-cutting contracts in `catalog/documents.toml`;
- preserve historical audits as historical evidence;
- preserve the frozen v26.9.1 proof corpus unless the change is explicitly to that future subject;
- never hand-edit generated status/SOC2/view Markdown;
- build mdBook and observe exact-head Pages CI before calling the documentation graph closed.

## Publishing a change

Use a purpose branch and draft PR by default. State:

- exact base/head identity;
- what changed and why;
- affected authority/evidence boundaries;
- commands/workflows actually executed and their results;
- blocks/exclusions;
- scoped standing.

A change without an executed verifier is changed, not verified. A green verifier for an earlier head does not prove a later head whose tree changed.

Do not merge, publish, deploy, rotate keys, or communicate externally unless that consequence is explicitly authorized.
