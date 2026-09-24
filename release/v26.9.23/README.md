# Chatman Ecosystem v26.9.23 release subject

This directory is the independent v26.9.23 release subject (CE23-1 in
`sjira/goal.ttl`). It is a ggen sub-project over the byte-identically vendored
`chatman-ecosystem-release-pack`. `release/v26.9.1` is its predecessor and is never
read or changed by it.

## Layout

| path | kind | owner |
|---|---|---|
| `ggen.toml` | sub-project config: vendored pack entry (`lock = true`) and `extra_ontologies` inputs | hand-written wiring |
| `release.ttl` | release-instance facts: version, the xaas and ggen_igniter components, role mappings | consumer-owned (pack law) |
| `imports/fleet-classification.ttl` | byte copy of xaas `docs/sjira/v26.9.23/fleet/classification.ttl` at the pinned xaas commit | import |
| `vendor/ggen-marketplace/` | vendored marketplace packs; `VENDOR.toml` records commit and tree per pack | byte copy |
| `out/`, `ggen.lock` | render of `ggen sync run`: manifest, crosswalks, requirements, role derivations, imported crowns | generated |
| `manifest.toml`, `constitutional-role-crosswalk.toml` | symlinks to `out/`, so `scripts/release_line.py` resolves the line | pointer |
| `sjira/` | CE23 governing graph, prose and compiled work orders | CE-INTAKE |
| `courts/` | gate courts named by `sjira/goal.ttl` | per gate |
| `bench/` | CE23-12 benchmark design capital | CE23-12 |

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

The court judges the exact committed head. Its clauses and its 15-mutant anti-vacuity corpus
are listed in `courts/ce23_1/court.py`, and its pins are in `courts/ce23_1/subject.toml`.

## See also

- `sjira/chatman-ce23.md`: the operator contract (CE23-0 .. CE23-11).
- `vendor/ggen-marketplace/packs/chatman-ecosystem-release-pack/README.md`: pack law, gates
  and templates.
- `../../HANDWRITTEN.md`: the residue ledger rows for this subject.
