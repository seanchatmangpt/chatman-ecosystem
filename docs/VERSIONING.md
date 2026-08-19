# Versioning and Documentation Currentness

## Version roles

The repository currently carries two different version subjects and they must not collapse:

| Version | Role | Current standing |
|---|---|---|
| `v26.8.18` | observed operational/documentation snapshot | `PARTIAL_ALIVE` |
| `v26.9.1` | next dependency-closed composition crown and frozen constitutional proof target | `PARTIAL_ALIVE` target corpus; not the current implementation snapshot |

`v26.8.18` answers **what is implemented and evidenced now?** `v26.9.1` answers **what exact composition and proof obligations must close next?**

## Exact-subject rule

A version label is not an identity. Any execution claim must bind to an exact subject such as a Git SHA, receipt digest, generated artifact digest, or external revision.

The v26.8.18 documentation review began at:

`1ed4972318467c5bfb5d283505893a361536d37a`

and explicitly admitted one direct descendant that materially changed the documented architecture:

`2d149b4091f6b5239ecfbbe054fdb0b2f5eb5f01`

The second commit adds the OCEL v2 accumulator/dashboard path and is therefore part of the reviewed v26.8.18 implementation baseline. This explicit admission is preferable to silently moving the review base.

## Currentness classes

### Current operational docs

Current operational docs may be rewritten when implementation evidence moves. They should carry a release label or exact-subject language where a claim depends on execution.

Examples: `README.md`, `ROADMAP.md`, `SESSION-FINAL-STATUS.md`, `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `docs/v26.8.18-release.md`, and the v26.8.18 operator docs.

### Constitutional docs

Constitutional law changes only when a falsifier or explicit architectural decision requires it. A newer implementation does not automatically mutate `CONSTITUTION.md` or frozen v26.9.1 mathematics.

### Historical docs

Audit and review documents preserve what was observed when they were authored. If later evidence invalidates a historical statement, append a correction or current-status pointer; do not erase the historical observation.

### Generated docs

Generated projections have no independent currentness. Their currentness is the currentness of their canonical input plus the generator execution that produced them. Never repair a generated Markdown file by hand.

## Version transitions

A release-documentation transition is lawful when:

1. the new exact implementation subject is identified;
2. changed capability/evidence edges are classified;
3. current operational docs are reconciled;
4. historical and future subjects are preserved;
5. generated projections are regenerated from canonical sources when required;
6. documentation build/link checks execute on the exact candidate head;
7. standing is not promoted beyond the strongest completed verifier.

## Standing is not semantic versioning

`ALIVE`, `PARTIAL_ALIVE`, `BUILD_BROKEN`, and the other standing values describe evidence state, not release age. A later version can have lower standing than an earlier exact subject. A green docs build proves representational closure for the built documentation subject; it does not prove the deployed platform or ecosystem composition is `ALIVE`.

## v0.1 language

Some older documents described a narrow `v0.1` control-plane boundary. That is historical architecture scope, not the current v26.8.18 implementation surface. Current operational docs should describe v26.8.18 and may mention v0.1 only as lineage. Historical evidence that accurately described v0.1 should remain historical.

## Falsifier

This versioning model is violated if a document uses one version's evidence to promote another version's subject without an explicit identity/transfer argument.
