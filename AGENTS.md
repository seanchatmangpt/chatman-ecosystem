# Engineering Standards Root Binding

> Generated adoption header. Shared engineering semantics are rooted at `seanchatmangpt/engineering-standards@5a3bb6446aeaee2255a7523d4d8cebf6042960c3`.

- Repository subject: `seanchatmangpt/chatman-ecosystem@c59596f5506e7a00ca4ed6b909ebf6d6659b74c1`
- Ecosystem role: ecosystem registry, orchestration, and cross-repository composition
- Adoption manifest: `engineering-standards.json`
- Project profile: `semantic/engineering-standards-profile.ttl`

The local constitution below remains authoritative for repository-specific mechanics. It may narrow the root but may not redefine shared WorkOrder identity, authority, receipt/replay, generated-artifact sovereignty, or evidence standing. Ticket, agent, capability, plan, proof, and generated output do not acquire ambient DO authority.

---

# Agent Operating Law

1. Read `CONSTITUTION.md`, `catalog/*.toml`, and applicable receipts before acting.
2. Name the exact repository subject for every claim.
3. Do not infer authority from tool access, credentials, repository ownership, or prior unrelated instructions.
4. Separate `OBSERVED`, `EXECUTED`, `CHANGED`, `VERIFIED`, and `EXCLUDED` evidence.
5. Route all external mutations through a brokered authority check.
6. Treat generated files as projections; modify canonical TOML or source instead.
7. Run the narrowest relevant test during implementation and `./scripts/crown.sh` before advancing Crown standing.
8. Never weaken, delete, or skip a negative fixture to obtain a green result.
9. Never claim `ALIVE` from prose, compilation alone, mock-only behavior, stale artifacts, or an HTTP success code without postcondition verification.
10. Merge, release, delete, communicate, spend, and approve only under explicit exact-scope authority.

---

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
