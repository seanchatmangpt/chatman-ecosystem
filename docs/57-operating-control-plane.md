# Operating the Composition Root

`chatman-ecosystem` is a **composition root**. It governs identities, dependencies, standing, portfolio observations, and release closure. It must resist the temptation to become the place where implementation code from every component is copied for convenience.

## Start with exact identity

Every operational session begins by resolving:

```text
repo = seanchatmangpt/chatman-ecosystem
base = exact ref/SHA
task = desired bounded outcome
acceptance = command / behavioral proof
constraints = authority, scope, dependency, evidence
```

The base should not move silently. If `main` changes after work begins, either preserve the original subject or explicitly reconcile the purpose branch onto the new base and re-run the exact-head verifier.

## Read doctrine before edits

The root `AGENTS.md` and `CONSTITUTION.md` are not decorative. They define the control laws for work in this repository. The operator should then inspect the applicable release manifest, candidate/fleet policy, status projection, receipts, tests, and owning workflow before manufacturing a change.

Generated projections are not the default editing surface. If a status page, generated portfolio view, or book chapter is derived from canonical source, repair the manufacturer or source instead of patching the projection to obtain a prettier diff.

## Release verification

The repository’s current release doctrine requires the non-crown checks:

```bash
python3 scripts/verify_release.py --check-refs
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

The final crown additionally requires:

```bash
python3 scripts/verify_release.py --check-refs --require-alive
```

These commands are deliberately stronger than “the TOML parses.” They bind release topology and exact-ref expectations into executable policy.

## Completion fanout

The composition root should construct **powerless completion intents**, not take implementation ownership from components. A completion packet can say:

- which component exact subject is admitted;
- current standing and evidence;
- unresolved mandatory predicate;
- dependencies and blocked dependents;
- narrowest owning verifier;
- suggested closure intent;
- receipt required for promotion.

It must not convert that packet into ambient authority to push, merge, deploy, revoke, bill, delete, or communicate on behalf of the owning system.

## Reconciliation law

A moving ecosystem inevitably creates branch and manifest drift. Reconciliation should preserve four distinctions:

1. **release lineage** — the exact subject admitted by the release;
2. **candidate lineage** — newer branches or PRs that may replace it;
3. **execution standing** — exact receipts bound to exact subjects;
4. **semantic equivalence** — when two trees or artifacts are proven equivalent under a specific relation.

Tree equivalence can transfer some structural evidence when explicitly admitted; it is not a universal substitute for exact-commit execution.

## Crown discipline

A crown is a conjunction. Do not promote the root because many sub-courts are green. Preserve red rails and typed blockers visibly. `BUILD_BROKEN`, `BLOCKED`, `UNKNOWN`, and `PARTIAL_ALIVE` are useful states because they retain causal information.

The correct operational response to a red rail is:

```text
preserve failure
    -> locate failed transition
    -> form new hypothesis
    -> repair narrowest cause
    -> encode permanent guard/falsifier
    -> rerun same boundary
    -> expand verification only after success
```

Rerunning an unchanged failure with no new hypothesis is noise.

## Pages and this book

The mdBook publication path is intentionally independent from release standing. A successful book build proves that the documentation projection is structurally renderable. A successful Pages deployment proves that the exact built projection was published. Neither promotes v26.9.1 components or the aggregate ecosystem release to ALIVE.

The book workflow therefore has two stages:

1. **build/validate** on pull requests and branch subjects;
2. **deploy** only from the admitted publication path on `main` (or an explicitly authorized manual dispatch), using GitHub Pages permissions scoped to the deployment job.

This preserves `documentation publication != product release`.

## Operational daily loop

A mature composition-root loop is short:

1. refresh exact observations;
2. calculate drift and standing changes;
3. collapse logical WIP;
4. identify the dependency-closed closure frontier;
5. manufacture powerless intents for owning repositories;
6. ingest new receipts;
7. replay/verify;
8. update release standing;
9. stop when no admitted enabled work remains.

The root should not generate work merely to remain busy. It should close the existing graph and admit new scope only when observation or constitutional evolution requires it.
