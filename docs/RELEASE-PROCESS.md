# Release Process

## Scope

This repository is a composition/control plane. A release document can admit identities and evidence; it does not automatically merge repositories, deploy infrastructure, publish packages, communicate externally, or grant production authority.

## Current and next subjects

- current operational snapshot: `v26.8.18`
- next dependency-closed composition target: `v26.9.1`

See `VERSIONING.md` for why these subjects coexist.

## Release object

A release candidate is not a branch name. It is an admitted graph of exact component identities and required evidence.

For each required component capture:

```text
repository
ref
exact SHA
role
required dependencies
standing
overifier
receipt/replay evidence
authority class
```

A mutable ref is navigation; the exact SHA is identity evidence.

## Current-repo documentation release

For changes confined to this repository:

1. resolve `main` to an exact SHA;
2. materialize/read applicable doctrine;
3. inventory canonical/generated/historical/future docs;
4. construct the bounded documentation diff;
5. if `main` moves, classify drift explicitly rather than silently rebasing claims;
6. verify the candidate documentation head;
7. publish on a purpose branch and draft PR;
8. observe exact-head CI;
9. promote documentation standing only as far as the executed verifier permits.

The v26.8.18 documentation pass used exactly this pattern: the review began at `1ed497...`; one direct descendant `2d149...` materially added OCEL process evidence and was explicitly admitted through a merge relation rather than hidden.

## Local admission commands

The repository's primary local Crown path is:

```bash
./scripts/crown.sh
```

The underlying release verifier for the v26.9.1 composition includes:

```bash
python3 scripts/verify_release.py
python3 scripts/verify_release.py --check-refs
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The strict future crown additionally requires:

```bash
python3 scripts/verify_release.py --check-refs --require-alive
```

Do not run `--require-alive` and then reinterpret an expected refusal as a defect when required components have not yet earned `ALIVE`.

## Verification ladder

Use the narrowest high-information verifier first, then expand:

```text
format/schema/link/doc build
-> unit
-> integration
-> exact-head workflow
-> live subject behavior
-> consequence verification
-> receipt/replay
-> class closure where claimed
```

A docs build is sufficient for “these docs render/link under mdBook” but not “the deployment they describe is healthy.”

## Generated projections

Before publication, generated projections must be checked for drift through their owning generator. Never hand-edit:

- `views/generated/*`;
- `status/*` generated Markdown;
- generated SOC 2 binder pages;
- other generated report/deck outputs.

If a projection is stale and regeneration cannot be lawfully executed in the current pass, disclose staleness rather than manually synchronizing prose.

## Draft PR publication

Default publication state is a draft PR. The PR should record:

- exact base/head identities;
- intentional files/scope;
- changed semantics;
- commands/workflows actually executed;
- known blocks and exclusions;
- current standing;
- any admitted head drift.

Do not merge unless explicitly authorized.

## CI

GitHub Actions is supplementary evidence. Status metadata without logs/owning acceptance behavior is not automatically proof. Exact-head matters: a green run for an earlier head cannot crown a later head whose tree changed.

## Release standing

Use the tagged standing vocabulary literally:

- `UNKNOWN`
- `PARTIAL_ALIVE`
- `ALIVE`
- `BLOCKED`
- `BUILD_BROKEN`
- `UNSUPPORTED`
- typed `REFUSED` where the owning transition lawfully rejects

A release cannot rise above its required dependency/edge closure. One green subsystem does not average away a broken mandatory edge.

## Publication authority

The following consequences remain separate operations and require their own authority/evidence:

- merge PR;
- tag release;
- publish package/container;
- deploy infrastructure/application;
- rotate credentials/keys;
- communicate release externally;
- approve risk/compliance acceptance.

## Release receipt

A final release receipt should state:

```text
identity:
  repo/ref/SHA/version
O:
  observations and known staleness
O*:
  admitted subject and exclusions
mu:
  exact changes/manufacture path
verification:
  commands/workflows/exits/results
receipts:
  digests/replay artifacts
standing:
  scoped result
publication:
  branch/commit/PR/tag if any
blocks:
  typed unresolved prerequisites
falsifiers:
  observations that would invalidate standing
```

## Falsifier

The release process is broken if a release can be promoted by mutable ref, prose assertion, generated-file existence, or CI status alone without the exact required subject/evidence relation.
