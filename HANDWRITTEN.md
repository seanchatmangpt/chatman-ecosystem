# HANDWRITTEN.md — hand-written product-surface ledger

Contract: every hand-written product artifact names its missing capability and
intended owner pack, and the ledger shrinks monotonically per milestone
(same contract as the xaas and ggen_igniter ledgers).

Format: `path | semantic element | missing capability | intended owner pack | date`

## Active

release/v26.9.23/sjira/goal.ttl | CE23 governing graph GC-CE-26.9.23 (lane CE-INTAKE; CE23 prose release/v26.9.23/sjira/chatman-ce23*.md): root, gates CE23-0 .. CE23-12, CE23-12 conjunct gates, successor bucket GC-CE-26.9.24, crown-equation stop query, two capabilities; zero work orders (all orders are compile_prose output) | UNSUPPORTED(generator-capability): no pack generates a GoalCheckpoint graph from an operator requirement table (the xaas GC-26.9.23 and GC-26.9.24 goal graphs are hand-authored the same way) | semantic-jira-pack (goal-graph projection from admitted gate propositions) | 2026-09-23
release/v26.9.23/sjira/unit_goal.py | per-prose-unit goal views of one multi-source goal graph (view root = common parent of the unit's gates, source pin, partition check) | UNSUPPORTED(generator-capability): the frozen compile_prose reads one root per --goal, pins one source digest and checks coverage of direct gates only (prose/root.rq, foreign_requirements.rq, uncovered_gates.rq); ggen_igniter is a frozen release subject for v26.9.23, so multi-unit goals cannot land there now | semantic-jira-pack (compile_prose multi-unit goals: transitive gate coverage + per-gate source pins; successor GC-26.9.24) | 2026-09-23
release/v26.9.23/sjira/corrections.py, release/v26.9.23/sjira/candidates/corrections.json | recorded corrections of the LLM extraction JSON (raw O kept byte-identical in candidates/raw/; corrected extraction = apply(raw, corrections)) | UNSUPPORTED(generator-capability): prose_spans.py (xaas, frozen) emits from one extraction JSON and has no correction ledger | xaas scripts/sjira first-mile tooling (correction ledger as an emit input; successor GC-26.9.24) | 2026-09-23
release/v26.9.23/sjira/compile_check.sh, release/v26.9.23/sjira/stop_witness.exs, release/v26.9.23/sjira/test_ce23_sjira.py | CE23 first-mile court (corrections, candidates, views, compile_prose --check, goal SHACL admission, court-script contract), oxigraph stop-query witness mirroring mix xaas.stop_court, Chicago tests | UNSUPPORTED(generator-capability): no pack renders a first-mile court or a stop witness for a goal graph outside xaas | semantic-jira-pack (first-mile court + stop evaluator template) | 2026-09-23
release/v26.9.23/courts/CE23-*.sh | 16 machinery-absent court stubs (print UNKNOWN, exit 75) named by goal.ttl sj:courtCommand | UNSUPPORTED(generator-capability): stubs are placeholders replaced by the machinery lanes of the generated CE23 wave | semantic-jira-pack (court stub projection from sj:courtCommand) | 2026-09-23
