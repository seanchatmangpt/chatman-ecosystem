# 54. Current Standing and Release Frontier

This chapter is intentionally **time-bounded**. It explains how to read the evidence surfaces carried by this source tree; it does not turn a fast-moving fleet into timeless prose.

The admitted v26.9.1 manifest in `release/v26.9.1/manifest.toml` records release standing as `UNKNOWN` and binds sixteen required component roles to exact repository/ref/SHA identities. Separately, the fleet status projection includes the composition root itself, producing seventeen tracked repository subjects.

## Fleet snapshot carried by this tree

The status projection observed at `2026-08-16T02:32:03.164547+00:00` reports:

| Standing | Repositories |
|---|---:|
| `ALIVE` | 2 |
| `PARTIAL_ALIVE` | 7 |
| `UNKNOWN` | 1 |
| `BLOCKED` | 1 |
| `BUILD_BROKEN` | 6 |

These numbers are **evidence states, not health percentages**. A `PARTIAL_ALIVE` repository can contain substantial proven capability while lacking the exact role-specific crown required by the release. A `BUILD_BROKEN` repository can have many independently ALIVE sub-capabilities while a mandatory broad rail remains red. A `BLOCKED` repository can have no source defect at all if execution is prevented before the owning verifier can run.

## Current role frontier in the projection

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

The authoritative live-in-repository files are `release/v26.9.1/manifest.toml`, `status/snapshot.json`, and the per-repository reports under `status/repos/`. This book does not replace them.

## Why the manifest and fleet observation can differ

The release manifest is an **admitted release instance**. A fleet survey is an **observation of repository state**. Head drift, newly observed workflow failures, new successful runs, or external branch movement can make the observation newer than the release manifest without automatically mutating release identity.

That distinction prevents an especially dangerous shortcut:

\[
\boxed{\text{latest branch head} \neq \text{admitted release subject}}
\]

A candidate head can be newer and better while still lacking admission into the release. Conversely, a release SHA can remain the correct identity even if a repository has moved beyond it.

## Book publication standing is independent

The first merged mdBook publication subject, `chatman-ecosystem@c5a9ef1e64fe24d1f332f838205931a69dc518d8`, executed the full book build court successfully: exact checkout, verified mdBook installation, graph validation, render, rendered-crown checks, and artifact preservation all passed. The production deployment then failed specifically at `Configure Pages` because the repository did not yet have GitHub Pages enabled for GitHub Actions.

That yields two independent propositions:

```text
BOOK_BUILD(c5a9ef1e...) = ALIVE
PAGES_PUBLICATION(c5a9ef1e...) = BLOCKED:PAGES_NOT_ENABLED
```

Neither proposition changes v26.9.1 release standing.

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

The ecosystem distinguishes at least four closure layers:

1. **epistemic closure** — observation is sufficiently admitted to support the claim;
2. **representational closure** — projections preserve intended semantics and are current;
3. **operational closure** — exact behavior executed, produced the required consequence, and was independently verified;
4. **class closure** — the solved class can transfer/reproduce without rediscovering the same reasoning.

Release closure composes those obligations across the required component graph. A green local test is therefore evidence only for the boundary it actually tests.

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
