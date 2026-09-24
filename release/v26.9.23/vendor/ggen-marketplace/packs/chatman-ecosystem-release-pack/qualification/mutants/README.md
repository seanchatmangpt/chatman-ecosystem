# Mutants

Each directory is a complete consumer: the mutant base (`../consumer-v26.9.23` without the CE
orders import, pack path `../../..`) plus exactly one mutation. `../qualify.sh` proves the base
passes both executors, so each refusal below is caused by its mutation. `EXPECTED.tsv` is the
machine-read contract (native code, native gate, runner verdict, runner reason).

| mutant | mutation (one change from the base) | refused by |
|---|---|---|
| M1-drop-crosswalk-row | `imports/legacy-v26.9.1.ttl` loses the lifted mfact component (the only supplier of formal-proof); an inner join would render 15 rows | native FM-PACK-013 gate 070 + runner (`role-without-disposition:formal-proof`) |
| M2-disposition-unclassified | `release.ttl` adds an explicit research row with `er:boundary er:ROLE_UNCLASSIFIED` | native gate 070 + runner (`unclassified-or-untyped-boundary:research`) |
| M3-court-reference-blocks-derivation | `imports/court-references.ttl` adds GC23-5 executing `seanchatmangpt/mfact`, so no rule derives formal-proof | native gate 070 + runner (also gate 080 `court-executed-repository-not-required-component`) |
| M4-drop-ggen_igniter-consistently | `release.ttl` drops the ggen_igniter component, xaas's dependsOn edge, the semantic-manufacture required role and its mapping; gates 010-075 pass | native gate 080 + runner (`critical-path-repository-not-required-component:ggen_igniter`) |
| M5-open-ontologies-critical-path | `imports/fleet-classification.ttl` reclassifies open-ontologies `sj:CriticalPath` | native gate 070 + runner (`required-role-not-supplied-by-target-release:public-ontology`; gate 080 too) |
| M6-hand-edited-rendered-file | `out/manifest.toml` is the base render with `standing = "UNKNOWN"` forged to `"ALIVE"` | native FM-WRITE-005 (no `force`: a differing file refuses the sync); the runner passes, the graph is untouched |
| M7-decision-overrides-classification | `release.ttl` adds an explicit decision for manufacture although ggen is classified | native gate 070 + runner (`decision-overrides-fleet-classification:manufacture:ggen`) |
| M8-decision-without-reason | `release.ttl` adds an explicit formal-proof decision with no `er:reason` | native gate 070 + runner (`disposition-without-reason:formal-proof`) |
| M9-role-unmapped | `release.ttl` drops the semantic-manufacture constitutional mapping | native gate 075 + runner (`release-role-unmapped:semantic-manufacture`) |
| M10-ambient-actuation | `release.ttl` drops `er:brceExclusive true` from the Actuate mapping | native gate 075 + runner (`ambient-actuation-mapping:execution-realization`) |
| M11-requirement-row-without-falsifier | `release.ttl` adds a checkpointed WorkOrder without base SHA or falsifier | native gate 085 + runner (`missing-falsifier-description`) |
| M12-classification-basename-collision | `imports/fleet-classification.ttl` adds a second row whose identifier is also `ggen` | native gate 070 + runner (`fleet-classification-basename-collision:ggen`) |

Revert check (receipt MP-RELPACK-XW): with gates 070, 075, 080 and 085 removed from a scratch
copy of the pack, all eleven graph mutants (M1-M5, M7-M12) sync with exit 0 and pass the
runner, and the M1 render still lists all 16 roles (formal-proof with an empty boundary), so
those refusals come from the new gates, not from the base.
