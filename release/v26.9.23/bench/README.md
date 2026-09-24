# CE23-12 benchmark design (v26.9.23)

CE23-12 for v26.9.23 = BenchmarkDesign AND MSAContract AND GeneratedQualificationPlan
(`../sjira/chatman-ce23-12-standings.md`): the release ships the measurement system and the
qualification contract of the DfLSS non-LLM operational benchmark (`../sjira/chatman-ce23-12-bench.md`),
not operational standing. The design's standing is derived only by the CE23-12 court receipt on an
exact subject: `sh release/v26.9.23/courts/CE23-12.sh` exit 0 = BENCHMARK_DESIGN_ALIVE.
NON_LLM_OPERATIONAL_ALIVE is UNKNOWN for every class (executed unseen members n = 0) and is never
implied by the design; the generated successor orders in `out/plan/` are the path to it.

## Layout

| path | kind | order |
|---|---|---|
| `DESIGN.md`, `ontology-draft.ttl`, `orders.json`, `candidates/` | design capital moved from the retired driver substrate (pinned in `../sjira/goal.ttl`; never edited) | - |
| `pack/` | the in-repo `nonllm-class-qualification-pack` 0.1.0: `ontology.ttl` (nlb: vocabulary, standing kinds, tier specs, plan vocabulary), `gates/*.rq` (SPARQL gates ggen enforces), `shacl/nlb-shapes.ttl`, `templates/*.tmpl` (projections and the plan CONSTRUCT), `scripts/` (kernel, lift, imports, verifiers, qualification driver) | BD-01/02/03 |
| `design.ttl` | the ce23: instance graph: 5 KNOWN_CANDIDATE classes with observed membership tests, independent verifiers and 21 near-misses, 15 kept classes, 15 CTQs, 7 RTY stages, 7 MSA properties and 12 MSA courts, 8 factors, 9 fault-injection points, 9 negative controls, 16 capability gaps, the plan node, crown thresholds, statistics definitions; every node traces to a committed operator-prose proposition | BD-06 |
| `bench.toml` | inputs and outputs of the non-ggen generators (kernel, lift, imports) | - |
| `imports/` | byte copies of the committed CE23-12 prose candidates, the CE23 goal graph and the prose-derived orders (ggen refuses `..` paths) | BD-05 |
| `generated/` | kernel output (`evidence-tiers.ttl`, `bound-table.ttl`: exact Clopper-Pearson bounds) and the lift of `orders.json` (`reference-orders.ttl`) | BD-03 |
| `ggen.toml`, `ggen.lock`, `out/` | the consumer and its render: class catalog, CTQ tracker, MSA contract, acceptance rules (md + json), DOE design / CI / factor-standing matrices, the generated B3 workflow, 30 case manifests, the qualification report, the SPC chart skeleton, the generated qualification plan (`out/plan/orders.ttl`, `ORDERS.md`) | BD-04/07/08 |

## Regenerate

```bash
cd release/v26.9.23/bench
python3 pack/scripts/import_inputs.py --consumer .          # byte copies into imports/
python3 pack/scripts/lift_reference_orders.py --consumer .  # generated/reference-orders.ttl
python3 pack/scripts/evidence_tiers.py --consumer .         # generated/evidence-tiers.ttl, bound-table.ttl
ggen sync run                                               # out/ (ggen 26.9.18); a second run writes nothing
```

Each script has `--check`. After a pack or input change delete `ggen.lock` and `out/`, then sync.
Never write Python bytecode into `pack/` (`PYTHONDONTWRITEBYTECODE=1`): ggen's pack content hash covers
every file under the pack directory. Pack qualification (five instruments, the court corpus):

```bash
python3 pack/scripts/verify.py --consumer . --mutations ../courts/ce23_12/mutations.toml --ggen
```

## Successor

The `nlb:` vocabulary, gates, shapes, templates and scripts stay in-repo for v26.9.23 (operator
directive 2026-09-23/24). Their successor home is `ggen-marketplace/packs/nonllm-class-qualification-pack`
(order CE23-12-BD-02), with the generic DfLSS terms (fractional-factorial design, factor support,
MSA study, control chart, capability result, evidence tier) upstreamed to `dflss-pack` 0.3.0
(CE23-12-BD-01); once published there, this directory vendors the pack byte-identically instead
(`release/v26.9.23/vendor/ggen-marketplace/VENDOR.toml` pattern). Executing the generated plan (the
OP-* reference orders) is successor goal `GC-CE-26.9.24` work.
