# Chatman Ecosystem v26.9.23 release subject

This directory is the independent v26.9.23 release subject (CE23-1 in
`sjira/goal.ttl`). It is a ggen sub-project over the byte-identically vendored
`chatman-ecosystem-release-pack`. `release/v26.9.1` is its predecessor and is never
changed by it; the render never reads it: its 16 roles enter only as `imports/legacy-v26.9.1.ttl`,
the committed lift of the manifest blob at the base commit (CE23-2).

## Layout

| path | kind | owner |
|---|---|---|
| `ggen.toml` | sub-project config: vendored pack entry (`lock = true`) and `extra_ontologies` inputs | hand-written wiring |
| `release.ttl` | release-instance facts: version, the xaas and ggen_igniter components, role mappings | consumer-owned (pack law) |
| `imports/fleet-classification.ttl` | byte copy of xaas `docs/sjira/v26.9.23/fleet/classification.ttl` at the pinned xaas commit | import |
| `imports/legacy-v26.9.1.ttl` | the pack's `lift/manifest_to_er.py` over the `release/v26.9.1/manifest.toml` blob of the base commit c59596f5 (CE23-2) | lifted import |
| `imports/court-references.ttl` | `courts/ce23_2/observe_court_refs.py`: which xaas GC-26.9.23 court scripts (at the xaas component commit) execute which repository (CE23-2) | observed import |
| `vendor/ggen-marketplace/` | vendored marketplace packs; `VENDOR.toml` records commit and tree per pack | byte copy |
| `out/`, `ggen.lock` | render of `ggen sync run`: manifest, crosswalks, requirements, role derivations, imported crowns | generated |
| `manifest.toml`, `constitutional-role-crosswalk.toml` | symlinks to `out/`, so `scripts/release_line.py` resolves the line | pointer |
| `sjira/` | CE23 governing graph, prose and compiled work orders | CE-INTAKE |
| `courts/` | gate courts named by `sjira/goal.ttl` | per gate |
| `courts/ce23_9/` | CE23-9 root court: judge (`court.py`), members (`members.py`), CI check universe (`ci_checks.py`), local CI job runner (`ci_job.py`), pins (`root.toml`, incl. the `[validator]` pin of the generated receipt validator, read at run time from ggen-marketplace and never committed here), the real base check-run fixture | CE23-9 |
| `bench/` | CE23-12 benchmark design: capital (`DESIGN.md`, `ontology-draft.ttl`, `orders.json`), the in-repo `nonllm-class-qualification-pack` (`bench/pack/`), the design graph `design.ttl` and its ggen projections (`bench/out/`) | CE23-12 |

## Regenerate

```bash
cd release/v26.9.23 && ggen sync run
```

A second run writes nothing. `ggen.lock` pins the vendored pack together with every
`extra_ontologies` input. After an intended input change (a re-vendored pack, a new
classification import, recompiled orders), delete `ggen.lock` and the stale `out/` files,
then sync again. Never edit `out/` or a vendored file: the next sync refuses a hand edit
(FM-WRITE-005) or vendored drift (FM-PACK-008).

## Court

```bash
sh release/v26.9.23/courts/CE23-1.sh
```

The court judges the exact committed head. Its clauses and its anti-vacuity corpus (24 refused mutants, the pending-publication edge
MV1p and the published control M0p)
are listed in `courts/ce23_1/court.py`, and its pins are in `courts/ce23_1/subject.toml`.

```bash
sh release/v26.9.23/courts/CE23-2.sh
```

The CE23-2 court judges the 16-role legacy crosswalk (`out/legacy-role-crosswalk.toml`,
`out/crosswalk.ttl`, `out/role-derivations.toml`): every required role of
`release/v26.9.1/manifest.toml`, read from the base blob, has exactly one row with REQUIRED,
SUCCESSOR, BLOCKED, UNSUPPORTED or REFUSED, its own legacy component and a derived or decided
provenance; both imports are re-derived byte for byte; the render reproduces twice. Clauses and the
18-mutant corpus: `courts/ce23_2/court.py`; pins and admitted decisions (none):
`courts/ce23_2/crosswalk.toml`. To refresh the court-reference import after a component re-pin:

```bash
cd release/v26.9.23 && python3 courts/ce23_2/observe_court_refs.py --subject . > imports/court-references.ttl
```

The CE23-12 courts judge the benchmark design (standing BENCHMARK_DESIGN_ALIVE on exit 0;
NON_LLM_OPERATIONAL_ALIVE stays UNKNOWN for every class, n = 0):

```bash
sh release/v26.9.23/courts/CE23-12.sh                              # crown: runs the three below
sh release/v26.9.23/courts/CE23-12-BenchmarkDesign.sh              # D and M: ontology, classes, trace
sh release/v26.9.23/courts/CE23-12-MSAContract.sh                  # MSA contract + MSA of the design
sh release/v26.9.23/courts/CE23-12-GeneratedQualificationPlan.sh   # DOE, statistics, generated orders
```

Clauses, the anti-vacuity corpora and the pins are in `courts/ce23_12/` (`court.py`, `mutations.toml`,
`pins.toml`); the design itself is documented in `bench/README.md`.

The CE23-9 exact-head root court is generated: its members are the `er:Gate` facts at the end of
`release.ttl`, rendered by the vendored pack (0.4.0) into `out/scripts/crown_v26_9_23.sh`, with the
typed non-success CI checks in `out/typed-checks.txt` and the re-hashed imports in
`out/receipts/IMPORTS.sha256`:

```bash
sh release/v26.9.23/courts/CE23-9.sh      # exit 0 ALIVE, 1 REFUSED, 75 UNKNOWN
```

Members, in order: `subject-clean`, `projection-drift` (release subject, bench, views/generated),
`manifest-refs`, the local CI members `ci.crown.fast`, `ci.crown.test` (unit/integration),
`ci.crown.cold-cache`, `ci.gall-crown`, `ci.release-control-plane`, `ci.old-estate-revops` (each runs
the committed job's `run:` steps at HEAD through `courts/ce23_9/ci_job.py`), `imported-receipts`,
`ci-dispositions`, `replay`, `exact-head-ci` and `chatman-stop` (CHATMAN_STOP; UNKNOWN on the
operator's GC23-12 acceptance edge while STOP=false). Every CI check the release pull request and main
carry is a local member, a typed `er:CheckDisposition` or judged by its exact-head check-run
(`members.py ci-dispositions` prints the table).

## See also

- `sjira/chatman-ce23.md`: the operator contract (CE23-0 .. CE23-11).
- `vendor/ggen-marketplace/packs/chatman-ecosystem-release-pack/README.md`: pack law, gates
  and templates.
- `../../HANDWRITTEN.md`: the residue ledger rows for this subject.
