# Chatman Ecosystem

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
