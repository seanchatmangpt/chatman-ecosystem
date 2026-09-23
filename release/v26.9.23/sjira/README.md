# CE23 first mile (Chatman Ecosystem v26.9.23)

The CE23 work orders are compiled from the operator prose through the v26.9.23 first-mile
pipeline, never hand-authored into a backlog (lane CE-INTAKE, wave CE0; xaas PRD PR-002..PR-005,
ARD sections 5, 17 and 24 M9). Everything below `compiled/`, `units/` and `candidates/*.ttl`
is generated; `sh compile_check.sh` recomputes all of it and exits 0 only on byte equality.

| step | input -> output | kind |
|---|---|---|
| prose | `chatman-ce23.md`, `chatman-ce23-12-bench.md`, `chatman-ce23-12-standings.md` | operator testimony, byte-identical |
| extract | prose -> `candidates/raw/<unit>.extract.json` | the one LLM edge, recorded with `extractedBy` |
| correct | raw + `candidates/corrections.json` -> `candidates/<unit>.extract.json` | `corrections.py` (deterministic) |
| emit | extraction -> `candidates/<unit>.ttl` (ce: namespace) | xaas `scripts/sjira/prose_spans.py` (frozen) |
| view | `goal.ttl` -> `units/<unit>.goal.ttl` | `unit_goal.py` (deterministic) |
| compile | prose + candidates + view -> `compiled/<unit>/{propositions,orders}.ttl` | ggen_igniter `mix semantic_jira.compile_prose` |

The goal graph `goal.ttl` holds the root `GC-CE-26.9.23`, gates CE23-0 .. CE23-12 (CE23-12 with
three conjunct gates), the successor bucket `GC-CE-26.9.24` and the crown-equation stop query.
It holds no work order and no receipt. Each gate names the prose that defines it
(`dcterms:source`, `sj:sourceSha256`), and each unit is compiled against the view of exactly the
gates it defines. The compiler therefore refuses (`uncovered_gate`) any gate that its prose does
not require.

Extraction identities: `chatman-ce23` was extracted by `llm:claude-opus-5-5@wave-CE0/CE-INTAKE`.
The bench and standings units reuse the extraction of the benchmark design run
(`llm:claude-opus-5-5@wf_a0af447e-5fa/bench:design`). No second LLM pass over the same revision
is permitted (ARD section 5.5). There are 30 recorded corrections, all of `required_by` or
`boundary_class`, and each states its reason from `chatman-ce23-12-standings.md`.

```sh
sh release/v26.9.23/sjira/compile_check.sh                  # the court (check)
sh release/v26.9.23/sjira/compile_check.sh --write OUTROOT  # manufacture into OUTROOT
python3 -m unittest discover -s release/v26.9.23/sjira -p 'test_*.py' -v
cd <ggen_igniter> && MIX_ENV=test mix run <repo>/release/v26.9.23/sjira/stop_witness.exs \
  <repo>/release/v26.9.23/sjira/goal.ttl CE23-0 ...          # oxigraph CHATMAN_STOP witness
```

The CE23-12 standing rule (`chatman-ce23-12-standings.md`): CE23-12 for v26.9.23 is
BENCHMARK_DESIGN_ALIVE = BenchmarkDesign ∧ MSAContract ∧ GeneratedQualificationPlan.
NON_LLM_OPERATIONAL_ALIVE is successor work and is never implied by the design.
