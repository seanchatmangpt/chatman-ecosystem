# HANDWRITTEN — receipt-provenance-unification-pack

Ledger of every byte in this pack that `ggen sync run` does not produce. Files under
`generated/` are projections of `ontology.ttl` through `templates/` and are never edited by
hand. Added by lane MP-RPV (v26.9.23; PRD 28, CE23-3, CE23-9).

| path | kind | standing | reason |
|---|---|---|---|
| `ontology.ttl` (dfcm_fleet_v1 section) | data: transcribed facts | UNSUPPORTED(generator-capability) | Field bindings, value forms, the implication rule and the resolution kinds are observations of `receipt.schema.json` / `validate_receipt.py` / `xaas.stop_court.ex`, each cited with `rp:sourceFile` + `rp:sourceLine` (gates 02 and 04). No generator derives JSON Schema keywords into this vocabulary today; a JSON-Schema-to-rp: importer is successor capital. |
| `ontology.ttl` (qualification suites) | data: declarations | UNSUPPORTED(generator-capability) | Three `rp:QualificationSuite` rows naming fixture directories and arguments; they are the input the runner template projects. |
| `templates/*.tmpl` | generator source | n/a | Template extensions are the generator itself (array/length/nullability keywords, conditional requirement, implication rules, broken terms, profiles, read-only git resolution, qualification runner). |
| `gates/04_dfcm_facts_cited_with_line.rq`, `gates/05_probes_read_only.rq` | admission queries | n/a | Pack gates (SELECT of violations), enforced natively by ggen as FM-PACK-013 when the pack is consumed through a `[packs]` entry, and by `bin/run-gates.py`. |
| `bin/run-gates.py` | reused code (byte copy) | n/a | Byte-identical copy of `packs/gym-autonomic-crown-pack/bin/run-gates.py` (sha256 `739d9819747b8a45d18e0bd11c0bcdccae7a7bf7ea14560eff28dada7c184ff5`); no new code. |
| `qualification/fixtures/**` | data: fixtures | UNSUPPORTED(generator-capability) | Real receipts and one-mutation variants of xaas `GC23-4.json`, plus two forged receipts copied byte for byte from the CE23-9 scans; derivation and sha256 of every file in `qualification/README.md`. |
| `pack.toml`, `PROVENANCE.md`, `HANDWRITTEN.md`, `qualification/README.md` | prose | n/a | Documentation. |
