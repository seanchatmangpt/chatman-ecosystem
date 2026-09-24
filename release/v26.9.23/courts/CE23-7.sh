#!/bin/sh
# CE23-7 court: Version-fence Chatman tooling (release/v26.9.23/sjira/goal.ttl ce:CE23-7).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE;
# exit 75 = machinery absent (standing UNKNOWN); any other exit = the court ran
# and witnessed nothing (standing UNKNOWN); exit 1 carries typed REFUSED[<code>]
# lines naming the counterexample.
# Machinery (lane CE23-7): release/v26.9.23/courts/ce23_7/court.py exercises
# verify_release, plan_completion, survey_portfolio, verify_standing_evidence,
# verify_west_workspace and release_line against release/v26.9.23 (explicit
# --release and a flipped catalog pointer; run from the subject and self-hosted in a
# tree whose pointer names v26.9.1), audits what each targeted run reads (PEP 578 hook,
# ce23_7/audit_run.py) wherever it lives, and refuses a v26.9.1 read by open, directory
# read, byte copy, child process, native call or URL; it reports UNKNOWN for what the
# hook cannot see into. It also refuses any silent v26.9.1 default, any changed v26.9.1
# output and any change to release/v26.9.1 itself (clauses F1-F8 in court.py; facts and
# pins in ce23_7/fence.toml; anti-vacuity corpus ce23_7/mutate.sh).
here=$(cd "$(dirname "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "UNKNOWN[TOOL_MISSING] CE23-7: python3 not on PATH"; exit 75; }
[ -f "$here/ce23_7/court.py" ] || { echo "UNKNOWN[MACHINERY_ABSENT] CE23-7: $here/ce23_7/court.py"; exit 75; }
exec python3 "$here/ce23_7/court.py" "$@"
