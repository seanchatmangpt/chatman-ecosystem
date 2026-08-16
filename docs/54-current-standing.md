# Current Standing and Release Frontier

This chapter is intentionally **time-bounded**. It does not attempt to freeze a fast-moving ecosystem into prose. Instead, it explains how to read the current evidence surfaces at the exact book base.

At book base `chatman-ecosystem@e1f5c8f116a6866f06e0cee7dce19539330c80db`, the admitted v26.9.1 manifest records release standing as `UNKNOWN`. Its release instance contains sixteen required component roles and exact repository/ref/SHA identities. Separately, the fleet status snapshot observed the composition root plus those component subjects and reported seventeen tracked repositories.

## Fleet snapshot at the book base

The repository status projection observed at `2026-08-16T02:32:03.164547+00:00` reports:

| Standing | Repositories |
|---|---:|
| `ALIVE` | 2 |
| `PARTIAL_ALIVE` | 7 |
| `UNKNOWN` | 1 |
| `BLOCKED` | 1 |
| `BUILD_BROKEN` | 6 |

These numbers are **evidence states, not health percentages**. A `PARTIAL_ALIVE` repository can contain substantial proven capability while lacking the exact role-specific crown required by the release. A `BUILD_BROKEN` repository can have many independently ALIVE sub-capabilities while a mandatory broad rail remains red. A `BLOCKED` repository can have no source defect at all if execution is prevented before the owning verifier can run.

## Current role frontier at the book base

| Repository | Release role | Snapshot standing |
|---|---|---|
| `open-ontologies` | public ontology | `BUILD_BROKEN` |
| `process-intelligence` | research | `PARTIAL_ALIVE` |
| `wasm4pm-compat` | process type law | `PARTIAL_ALIVE` |
| `star-toml` | config admission | `BUILD_BROKEN` |
| `ggen` | manufacture | `PARTIAL_ALIVE` |
| `ggen-marketplace` | pack marketplace | `PARTIAL_ALIVE` |
| `mfact` | formal proof | `PARTIAL_ALIVE` |
| `bcinr` | CMCA kernel | `BUILD_BROKEN` |
| `mfw` | orchestration | `BLOCKED` |
| `gymact` | actuation | `BUILD_BROKEN` |
| `autofde-lab` | explore | `BUILD_BROKEN` |
| `wasm4pm` | process execution | `UNKNOWN` |
| `affidavit` | provenance | `ALIVE` |
| `praxis` | fleet conformance | `BUILD_BROKEN` |
| `autofde` | product | `ALIVE` |
| `fdegym` | capstone | `PARTIAL_ALIVE` |
| `chatman-ecosystem` | constitutional root | `PARTIAL_ALIVE` in the status projection |

The authoritative current files are `release/v26.9.1/manifest.toml`, `status/snapshot.json`, and the per-repository reports under `status/repos/`. The book does not replace them.

## Why the manifest and the live snapshot can differ

The release manifest is an **admitted release instance**. A fleet survey is an **observation of current repository state**. Head drift, newly observed workflow failures, new successful runs, or external branch movement can make the observation newer than the release manifest without automatically mutating release identity.

That distinction prevents an especially dangerous shortcut:

\[
\boxed{\text{latest branch head} \neq \text{admitted release subject}}
\]

A candidate head can be newer and better while still lacking admission into the release. Conversely, a release SHA can remain the correct identity even if a repository has moved beyond it.

## The release crown is conjunctive

The release crown is deliberately harder than “most components look good.” For required rails \(r_i\):

\[
Release=ALIVE
\iff
\bigwedge_i ALIVE(r_i)
\land ExactSubjectAgreement
\land ReceiptIntegrity
\land Replay
\land BoundaryPreservation.
\]

One blocked mandatory rail is enough to prevent the aggregate crown. This is not pessimism; it is type safety for claims.

## Standing is local to evidence

A useful way to read standing is as a scoped proposition:

```text
ALIVE(subject, boundary, verifier, context, receipt)
```

not as a permanent adjective attached to a repository name. If the exact subject moves, execution standing does not automatically follow. If a verifier changes, its prior receipt cannot silently validate the new verifier. If the boundary changes, the old proof may remain true but no longer answer the new question.

## Release closure versus capability closure

The ecosystem now distinguishes at least four closure layers:

1. **epistemic closure** — the observation is sufficiently admitted to support the claim;
2. **representational closure** — projections preserve the intended semantics and are current;
3. **operational closure** — the exact behavior executed, produced the required consequence, and was independently verified;
4. **class closure** — the solved class can be transferred/reproduced without rediscovering the same reasoning.

Release closure composes those obligations across the required component graph. A green local test is therefore necessary only for the boundary it actually tests.

## The next release frontier

The correct completion algorithm is dependency-closed rather than breadth-first “make everything green.” The composition root should continuously identify the minimal unresolved subjects that block the most downstream required roles, then construct reversible closure intents for those subjects.

Conceptually:

\[
\text{NextWork}
=
\arg\max_{w\in WIP}
\frac{\text{downstream impact closed}(w)}{\text{cost/risk}(w)}
\]

subject to authority, exact identity, dependency, and evidence constraints.

The release should become `ALIVE` only when that frontier is empty under the admitted definition of done—not when the narrative feels complete.
