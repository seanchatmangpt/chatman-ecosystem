# Chatman Ecosystem release doctrine

This repository is the composition root, not an implementation monolith.

## Preserve

- Preserve repository ownership boundaries.
- Preserve exact repository/ref/SHA identity for release components.
- Preserve `UNKNOWN != ALIVE`, inspection != execution, and workflow existence != successful run.
- Preserve SELECT, CONSTRUCT, and DO as separate authority classes.
- Preserve zero unreceipted actuation: this repository grants no ambient DO authority.

## Release graph

`release/v26.9.1/manifest.toml` is the v26.9.1 admitted component graph.

A required component must have:

- one canonical component id;
- one `owner/repo` coordinate;
- one branch ref;
- one exact 40-character commit SHA;
- one release role;
- one standing value;
- explicit dependencies contained in the same manifest.

No required dependency may be implicit. No dependency cycle is admitted.

## Standing

Use only:

- `UNKNOWN`
- `PARTIAL_ALIVE`
- `ALIVE`
- `BLOCKED`
- `BUILD_BROKEN`
- `UNSUPPORTED`

A Git SHA is identity evidence, not ALIVE evidence. Promote a component to `ALIVE` only after observed execution of the exact admitted subject under its owning verifier, with the owning receipt/replay evidence.

## Changes

Prefer additive, reversible release-control changes. Do not copy implementation code from component repositories into this repository. Generated reports are projections and do not outrank the manifest or owning repository evidence.

Before publication, run:

```bash
python3 scripts/verify_release.py --check-refs
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The final release crown additionally requires:

```bash
python3 scripts/verify_release.py --check-refs --require-alive
```
