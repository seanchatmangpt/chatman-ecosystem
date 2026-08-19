# Documentation Maintenance

## Goal

Documentation is part of the evidence system. It must distinguish current truth, frozen doctrine, historical observation, and generated projection so prose cannot silently acquire authority it does not have.

## Sources of truth

| Surface | Source of truth |
|---|---|
| constitutional laws | `CONSTITUTION.md` + canonical implementation/tests |
| cross-cutting document registry | `catalog/documents.toml` |
| mdBook publication graph | `docs/SUMMARY.md` |
| current release snapshot | `docs/v26.8.18-release.md` |
| current architecture/operations | `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md` |
| generated rail/portfolio views | canonical catalog + generator, never Markdown edits |
| fleet status | `status/snapshot.json` + status generator |
| SOC 2 binder | ontology/ggen pack inputs + generator |
| v26.9.1 proof doctrine | `docs/v26.9.1/00_CANONICAL_INDEX.md` and its frozen corpus |
| nested post-AGI handbook | `docs/post-agi-platform-handbook/SUMMARY.md` |

## Adding a document

For a new cross-cutting document:

1. classify it (`CANONICAL`, `CURRENT`, `HISTORICAL`, `GENERATED`, `FUTURE`, `LOCAL`);
2. choose the owning source/subject;
3. add it to `docs/DOCUMENTATION-INVENTORY.md`;
4. add it to `docs/SUMMARY.md` if it belongs in the main mdBook;
5. add it to `catalog/documents.toml` when it is a cross-cutting operational/constitutional/release contract;
6. link it from the nearest owning landing page;
7. run the docs build/link checks;
8. record exact-head CI before claiming documentation closure.

## Updating a current doc

Before editing, answer:

- What exact implementation subject is this claim about?
- Is the claim observed, inferred, or future?
- Is there a newer canonical source?
- Is the file generated?
- Will this rewrite erase historical evidence?

If the exact subject moved, state the movement explicitly. Do not use “latest” as a substitute for SHA/revision identity in evidence-sensitive claims.

## Historical evidence

Audits, session notes, incident records and gap reviews should be preserved. When later work closes a historical gap, prefer an appended/current pointer such as:

```text
Historical observation: X was missing at SHA A.
Current status: X was implemented at SHA B; see current release doc Y.
```

Do not rewrite the earlier observation to say X always existed.

## Generated documentation

Generated output is a projection. Forbidden maintenance pattern:

```text
notice generated table stale
-> edit Markdown by hand
-> commit green-looking table
```

Required pattern:

```text
notice projection stale
-> identify canonical input/generator
-> repair canonical input if needed
-> run generator
-> run drift check
-> commit source + generated projection according to repo policy
```

If regeneration is blocked, disclose `STALE/UNKNOWN` and preserve the old generated output.

## Version labels

Use `v26.8.18` for current operational docs in this release pass. Preserve `v26.9.1` in future/frozen proof documents. Do not global-search-and-replace version strings across the repository.

Version-specific assertions should say whether they refer to:

- implementation snapshot;
- target release graph;
- historical observation;
- conceptual/frozen doctrine.

## Documentation review checklist

### Identity
- exact repo/ref/SHA or explicit non-execution scope where needed;
- version role correctly classified.

### Semantics
- no `Candidate == Admitted` collapse;
- no `Proof == Authority` collapse;
- no `CONSTRUCT == DO` collapse;
- no `derivation receipt == actuation receipt` collapse;
- no mechanism -> scale/compliance/SLA overclaim.

### Links/navigation
- main docs landing page points to current operational docs;
- mdBook `SUMMARY.md` includes every intended book page;
- nested book summaries remain intact;
- Jira/audit/future corpora have explicit indexes.

### Generated-state hygiene
- no hand edits to generated Markdown;
- stale projection disclosed or regenerated;
- catalog registry matches cross-cutting documents.

### Evidence language
Prefer:

- “observed at exact subject”
- “executed command/result”
- “verified postcondition”
- “inferred from X and Y”
- “not verified / blocked / unsupported”

Avoid:

- “production-ready” without a defined acceptance relation;
- “fully live” when one required edge is incomplete;
- “compliant/certified” without the external authority/evidence;
- “HA/multi-region” for single-node/cold-standby mechanisms.

## Documentation Definition of Done

A documentation change is `ALIVE` for its own representational subject only when:

1. all intended pages exist;
2. navigation includes them;
3. canonical registry is consistent;
4. generated-file boundaries are preserved;
5. version/currentness is explicit;
6. the docs build/link verifier executes successfully on the exact candidate head;
7. no required documentation gate fails.

This standing is scoped to documentation. It does not promote the software/deployment subject described by the docs.

## Periodic maintenance

At release boundaries:

1. regenerate/document inventory from the repository tree;
2. compare current implementation surface to operator docs;
3. inspect historical docs for current-status pointers, not rewrites;
4. inspect generated projections for drift;
5. check `catalog/documents.toml` paths;
6. build mdBook;
7. capture exact-head CI receipt;
8. update `docs/v26.x.y-release.md`.

## Falsifier

The documentation system is not closed if a user must inspect commit history to learn a current operator-critical fact that has no owning current document, or if two current documents make contradictory claims about the same exact subject.
