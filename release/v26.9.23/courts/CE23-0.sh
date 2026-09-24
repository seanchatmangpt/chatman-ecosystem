#!/bin/sh
# CE23-0 court: Re-establish root identity (release/v26.9.23/sjira/goal.ttl ce:CE23-0).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE; exit 75 = UNKNOWN (a
# tool absent, the GitHub remote unreachable or not fetched, the lineage evidence absent from this
# checkout, or the pinned receipt validator unavailable; nothing refused); exit 1 carries typed
# REFUSED[<code>] lines naming the counterexample; any other exit = the court ran and witnessed
# nothing (standing UNKNOWN).
# Machinery (step CE23-0): release/v26.9.23/courts/ce23_0/court.py judges the canonical checkout's
# exact committed head: origin is github.com/seanchatmangpt/chatman-ecosystem and a live ls-remote
# puts the release base on GitHub main; the head descends from the base with the GitHub root alone
# and fast-forwards (or is) the published line; the pre-migration local-only lineage and the
# retired shadow clone's refs hold their pinned SHAs under the archive namespaces, and merge-base
# recomputes their relation to the base and the head; the er:Component + er:RefObservation fact
# passes the vendored release pack's gates; a sealed court-emitted receipt's claims replay; then
# the anti-vacuity corpus on synthetic repositories. Pins: release/v26.9.23/courts/ce23_0/identity.toml.
# Seal: --receipt-out receipts/v26.9.23/CE23-0.json --identity-out receipts/v26.9.23/CE23-0.identity.ttl
here=$(cd "$(dirname "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "UNKNOWN[TOOL_MISSING] CE23-0: python3 not on PATH"; exit 75; }
[ -f "$here/ce23_0/court.py" ] || { echo "UNKNOWN[MACHINERY_ABSENT] CE23-0: $here/ce23_0/court.py"; exit 75; }
PYTHONDONTWRITEBYTECODE=1 exec python3 "$here/ce23_0/court.py" "$@"
