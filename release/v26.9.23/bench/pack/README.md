# nonllm-class-qualification-pack 0.1.0

DfLSS qualification law for work classes claimed KNOWN (non-LLM): a design standing
(BENCHMARK_DESIGN_ALIVE) that never implies the operational standing (NON_LLM_OPERATIONAL_ALIVE),
evidence tuples typed by volume (tiers 30 / 100 / 300 / 3000 with exact one-sided Clopper-Pearson
bounds), fractional-factorial designs whose unsupported factors never enter a run, an MSA contract,
and a generated qualification plan of semantic-jira work orders.

Home: in-repo for Chatman Ecosystem v26.9.23 (`release/v26.9.23/bench/pack`). Successor home:
`ggen-marketplace/packs/nonllm-class-qualification-pack` (see `../README.md`, "Successor").

| path | content |
|---|---|
| `ontology.ttl` | nlb: vocabulary, standing kinds, tier specifications (inputs only), plan vocabulary |
| `gates/010..100_*.rq` | SELECT-violation gates ggen enforces on every sync (100 runs after the plan CONSTRUCT) |
| `shacl/nlb-shapes.ttl` | the same laws as SHACL (pyshacl) |
| `templates/*.tmpl` | projections; `plan-orders.ttl.tmpl` carries the plan CONSTRUCT |
| `scripts/evidence_tiers.py` | the single-mu statistics kernel (tiers, BoundRows, threshold sizes) |
| `scripts/lift_reference_orders.py`, `scripts/import_inputs.py` | reference-order lift; byte-identical imports |
| `scripts/doe_verify.py` | independent design-matrix verifier (resolution, aliasing, OS never varied) |
| `scripts/native_predicates.py` | the laws as imperative Python (independent instrument) |
| `scripts/verify.py` | qualification driver: five instruments over a fixture/mutant corpus |

Hand-written residue (declared): the scripts above (kernel and verifiers are the single mu and the
independent instruments; SPARQL 1.1 cannot compute pow/log and ggen has no SHACL stage for sh:sparql
constraints), and every template body (templates are the generator).
