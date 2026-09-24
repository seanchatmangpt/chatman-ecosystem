#!/bin/sh
# CE23-1 court: Create an independent v26.9.23 release subject (release/v26.9.23/sjira/goal.ttl ce:CE23-1).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE;
# exit 75 = machinery or a canonical checkout absent, or a vendored marketplace pin on a
# fast-forward of its published line awaiting that line's push (standing UNKNOWN); exit 1 carries
# typed REFUSED[<code>] lines naming the counterexample; any other exit = the court ran
# and witnessed nothing (standing UNKNOWN).
# Machinery (lane CE23-1): release/v26.9.23/courts/ce23_1/court.py judges the exact
# committed head: release/v26.9.1 is the pre-v26.9.23 tree (base c59596f5, pinned tree and
# manifest digest, clean checkout); the subject release/v26.9.23 (ggen.toml, release.ttl,
# imports/, the byte-identically vendored chatman-ecosystem-release-pack) is committed and
# self-contained (ggen.toml closed-world, every read path a committed regular entry, no
# symlink beyond the two line pointers), the judging court is the head's own, its
# render out/ + ggen.lock reproduces byte for byte under ggen and the pack's rdflib gate
# runner, the imported fleet classification is the byte copy its source names, every
# CriticalPath repository is a required component on its ref, verify_release --release
# v26.9.23 admits the rendered manifest, requirements.toml keeps every compiled order; then
# the anti-vacuity corpus (control ALIVE, 24 mutants in synthetic git repos refused; on synthetic
# marketplaces over the canonical objects the published control M0p is ALIVE and the pending-
# publication edge MV1p UNKNOWN, never refused).
# Pins: ce23_1/subject.toml; vendored pack provenance: release/v26.9.23/vendor/ggen-marketplace/VENDOR.toml.
here=$(cd "$(dirname "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "UNKNOWN[TOOL_MISSING] CE23-1: python3 not on PATH"; exit 75; }
[ -f "$here/ce23_1/court.py" ] || { echo "UNKNOWN[MACHINERY_ABSENT] CE23-1: $here/ce23_1/court.py"; exit 75; }
PYTHONDONTWRITEBYTECODE=1 exec python3 "$here/ce23_1/court.py" "$@"
