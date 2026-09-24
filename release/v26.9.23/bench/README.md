# CE23-12 benchmark design capital (v26.9.23)

Moved here on 2026-09-24 from the retired driver substrate (`~/wt/v26922/v26923/bench/`, preserved in
this repository at `refs/archive/pre-single-repo-migration/20260924T0600Z/shadow-files`) by the
operator-directed single-repo migration: design documents belong to the repository that owns the
requirement (CE23-12, `release/v26.9.23/sjira/chatman-ce23-12-*.md`).

Standing: **candidate** design capital, not an admitted release artifact. `BENCHMARK_DESIGN_ALIVE` is
UNKNOWN until orders CE23-12-BD-01..09 (`orders.json`) land and `courts/CE23-12-BenchmarkDesign.sh`,
`courts/CE23-12-MSAContract.sh` and `courts/CE23-12-GeneratedQualificationPlan.sh` pass.
`NON_LLM_OPERATIONAL_ALIVE` is UNKNOWN for every class (executed unseen members n = 0).

| file | content |
|---|---|
| `DESIGN.md` | the DMADV design: two standings, CTQs, MSA contract, DOE (OS factor UNSUPPORTED), evidence tiers N 30/100/300/3000 |
| `ontology-draft.ttl` | vocabulary + instance draft (`nlb:` target: a ggen-marketplace qualification pack; `ce23:` instances: `design.ttl` here) |
| `orders.json` | orders CE23-12-BD-01..09 (in scope) and OP-* (successor, out of scope for v26.9.23) |
| `candidates/` | proposition candidates extracted from the CE23-12 prose (first-mile LLM edge, recorded) |

Paths inside `DESIGN.md` that name `/private/tmp/...` or `~/wt/...` are historical evidence locations.
