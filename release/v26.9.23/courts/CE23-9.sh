#!/bin/sh
# CE23-9 court: Exact-head root court (release/v26.9.23/sjira/goal.ttl ce:CE23-9).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE; exit 75 = UNKNOWN
# (a tool, the rendered court, exact-head CI of an unpublished head, or the operator's GC23-12
# acceptance edge behind CHATMAN_STOP; nothing refused); exit 1 carries typed REFUSED[<code>] lines
# naming the counterexample; any other exit = the court ran and witnessed nothing (standing UNKNOWN).
# Machinery (step CE23-9): the members are er:Gate facts of release/v26.9.23/release.ttl, rendered by
# the vendored chatman-ecosystem-release-pack 0.4.0 into release/v26.9.23/out/scripts/crown_v26_9_23.sh
# (generated-projection drift, manifest/ref validation, every local CI crown member incl. unit/
# integration, imported receipt validation, CI dispositions, replay, exact-head CI, CHATMAN_STOP);
# release/v26.9.23/courts/ce23_9/court.py runs that rendered court on the exact committed head, types
# every member and runs the anti-vacuity corpus. Pins: release/v26.9.23/courts/ce23_9/root.toml.
here=$(cd "$(dirname "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "UNKNOWN[TOOL_MISSING] CE23-9: python3 not on PATH"; exit 75; }
[ -f "$here/ce23_9/court.py" ] || { echo "UNKNOWN[MACHINERY_ABSENT] CE23-9: $here/ce23_9/court.py"; exit 75; }
PYTHONDONTWRITEBYTECODE=1 exec python3 "$here/ce23_9/court.py" "$@"
