#!/bin/sh
# CE23-12 court: DfLSS non-LLM benchmark design crown (release/v26.9.23/sjira/goal.ttl ce:CE23-12).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE; exit 75 = machinery,
# a tool or a canonical checkout absent (standing UNKNOWN); exit 1 carries typed REFUSED[<code>] lines
# naming the counterexample; any other exit = the court ran and witnessed nothing (standing UNKNOWN).
# Machinery (step CE23-12, order CE23-12-BD-09): release/v26.9.23/courts/ce23_12/court.py crown.
# CE23-12 for v26.9.23 = BenchmarkDesign AND MSAContract AND GeneratedQualificationPlan
# (chatman-ce23-12-standings.md): the crown runs the three conjunct courts on the same exact head, admits
# each receipt only when it is ALIVE, names this head and its bench tree, and records
# non_llm_operational UNKNOWN (n = 0) for every KNOWN_CANDIDATE class with the OS factor UNSUPPORTED;
# every proposition required by CE23-12 is traced (T1); no operational standing is implied (X2).
# Standing on exit 0: BENCHMARK_DESIGN_ALIVE. NON_LLM_OPERATIONAL_ALIVE is never implied.
here=$(cd "$(dirname "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "UNKNOWN[TOOL_MISSING] CE23-12: python3 not on PATH"; exit 75; }
[ -f "$here/ce23_12/court.py" ] || { echo "UNKNOWN[MACHINERY_ABSENT] CE23-12: $here/ce23_12/court.py"; exit 75; }
PYTHONDONTWRITEBYTECODE=1 exec python3 "$here/ce23_12/court.py" crown "$@"
