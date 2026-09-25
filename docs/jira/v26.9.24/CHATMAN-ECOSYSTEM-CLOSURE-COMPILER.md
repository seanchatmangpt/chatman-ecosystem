# v26.9.24 Ecosystem Closure Compiler

**Canonical source:** `release/v26.9.24/closure.toml`
**Compiler:** `python3 -m scripts.release_train.ecosystem_closure` (pure; no network, no subprocess)
**Projection:** `release/v26.9.24/closure-receipt.json` (must replay byte-identically)
**Standing:** `BLOCKED` (declared = computed)

## Why

The v26.9.24 estate is substantially built; what it lacks is **admitted single-head
composition**. Capabilities are spread across open, draft, conflicting, and superseded
PRs. This compiler takes those branches and PRs and produces one exact-SHA dependency
graph. It refuses the crown until every required edge can be replayed.

Closure set (the ontology `E`, spine in order):

```
N_BRCE -> T_SA2A -> W_sJira -> V_GALL -> X_XaaS -> D_zcode -> R_Affidavit -> C_Chatman
engineering-standards, ash-a2a, ggen-igniter, beam4pm, xaas, zcode-cli, affidavit, chatman-ecosystem
```

The following are required non-spine subjects:

- **Manufacture:** ggen, ggen-marketplace, ggen-ecosystem.
- **Prove/observe:** wasm4pm, ash-r2rml, ash-surface, ash-planning-center.

The following are advisory subjects. No required subject may depend on them:

- **Explore:** autofde-lab, gymact.
- **Application:** chatgpt-cloud-elixir, zoela/GodsLaw, mfw.

The other ~300 repositories under the account are outside the closure. Admitting them
would destroy the ontology.

## Stopping condition

```
forall r in E_required:
  exists! SHA_r  and  FINAL(r)  and  V(SHA_r) = PASS
  and  Dep(r) subset E_admitted (pinned by exact SHA)  and  R_r replayable
then C(E) = PASS
```

## Refusal law

| Law | Code(s) |
|---|---|
| More than one unresolved successor | `CLOSURE_SUCCESSOR_AMBIGUOUS`, `CLOSURE_CANONICAL_PR_AMBIGUOUS`, `CLOSURE_SUPERSEDED_LINEAGE_OPEN`, `CLOSURE_ZOMBIE_LINEAGE_OPEN`, `CLOSURE_EXTRACTION_PENDING`, `CLOSURE_LINEAGE_UNENUMERATED` |
| Exactly one admitted head per repo | `CLOSURE_DUPLICATE_REPOSITORY`, `CLOSURE_SUBJECT_UNRESOLVED`, `CLOSURE_CANONICAL_SUBJECT_SPLIT`, `CLOSURE_CANONICAL_BINDING_ABSENT` |
| Non-mergeable / non-final required head | `CLOSURE_HEAD_NOT_MERGEABLE`, `CLOSURE_MERGEABILITY_UNKNOWN`, `CLOSURE_HEAD_NOT_FINAL`, `CLOSURE_HEAD_DRAFT` |
| Draft normative RFC | `CLOSURE_NORMATIVE_RFC_DRAFT`, `CLOSURE_NORMATIVE_ROOT_NOT_ADMITTED` |
| Red exact-head verification | `CLOSURE_VERIFICATION_NOT_GREEN`, `CLOSURE_VERIFICATION_SUBJECT_SPLIT` |
| UNKNOWN required proposition | `CLOSURE_PROPOSITION_UNKNOWN`, `CLOSURE_PROPOSITION_FAILED`, `CLOSURE_PROPOSITIONS_EMPTY` |
| Dependency SHA not in manifest | `CLOSURE_DEPENDENCY_SHA_UNBOUND`, `CLOSURE_DEPENDENCY_SHA_SPLIT`, `CLOSURE_DEPENDENCY_NOT_ADMITTED`, `CLOSURE_DEPENDENCY_NOT_REQUIRED`, `CLOSURE_DEPENDENCY_CYCLE` |
| Receipt / replay | `CLOSURE_RECEIPT_MISSING`, `CLOSURE_RECEIPT_NOT_REPLAYED` |
| Aggregate shadow release | `CLOSURE_SCOPE_EXCEEDS_BOUND` (`max_canonical_additions`) |
| Spine topology | `CLOSURE_SPINE_EDGE_MISSING`, `CLOSURE_SPINE_NOT_CROWNED`, `CLOSURE_ROOT_NOT_ADMITTED` |
| Narrative ALIVE | `CLOSURE_STANDING_OVERCLAIM` (exit 1 even without `--require-alive`) |

Each law has a negative fixture in `tests/release_train/ecosystem_closure/test_compiler.py`.

## Evidence classes in the manifest

- **OBSERVED** means read with `git ls-remote` at `closure.observed_at`. This covers:
  - every `sha`, every `default_head`, and every `lineage[].sha`;
  - HEAD and `refs/pull/<n>/head`.

  zoela and mfw refused anonymous ls-remote, so their SHAs are `UNRESOLVED`.
- **OPERATOR** means taken from the v26.9.24 operator evaluation. This covers:
  - PR state, draft, mergeable, and additions;
  - verifier conclusions and proposition states.

  `UNKNOWN` means the value was not observed. It is never promoted.
- **DECLARED** covers the `depends_on` edges. They come from the ontology `E`, not from
  package manifests.
- **UNBOUND** covers `dependency_shas` and receipt digests. Every one is empty today. That
  is the truth: no owning repository's pins or seals have been bound into this closure yet.

## Current verdict

- **Computed standing:** `BLOCKED`. All 15 required subjects are blocked.
- **ggen:** holds ALIVE(subject) in its own repository. The compiler refused an `ALIVE`
  declaration here (`CLOSURE_STANDING_OVERCLAIM`) because the semantic-pack seal digest and
  replay are not bound into the closure. The manifest declares `PARTIAL_ALIVE` until they
  are.

The compiler derives the repair order mechanically. It works dependencies first and
breaks ties by spine criticality:

```
engineering-standards -> ash-a2a -> ggen -> ggen-igniter -> beam4pm -> xaas -> zcode-cli
-> affidavit -> ash-r2rml -> ash-planning-center -> ash-surface -> ggen-marketplace
-> ggen-ecosystem -> wasm4pm -> chatman-ecosystem
```

## How a subject advances

Edit only `closure.toml`, then regenerate the projection with this command:

```bash
PYTHONPATH=. python3 -m scripts.release_train.ecosystem_closure \
  release/v26.9.24/closure.toml --emit release/v26.9.24/closure-receipt.json
```

A subject computes `ALIVE` only when all of the following hold:

- its canonical PR is `MERGED` and it is the only open lineage;
- its verifier conclusion is `SUCCESS` at `run_head_sha == sha`;
- every proposition is `PASS`;
- every dependency is pinned in `dependency_shas` to the admitted SHA;
- its receipt digest is a `sha256:` value and its replay is `PASS`.

## Crown and falsifier

`scripts/crown.sh` runs the compiler with `--replay ... --require-alive` and refuses unless
the closure computes `ALIVE`.

The BLOCKED evaluation can be falsified. It is false if chatman-ecosystem can do all of
the following:

- consume this single manifest;
- check out every exact SHA into clean canonical repos;
- execute the declared verification chain;
- produce one receipt graph and replay it with no source reconstruction;
- get every crown court green.

If so, `--require-alive` exits 0 and v26.9.24 is ALIVE.
