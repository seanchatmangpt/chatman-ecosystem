#!/bin/sh
# CE23-12-MSAContract court: CE23-12 conjunct MSAContract (release/v26.9.23/sjira/goal.ttl ce:CE23-12-MSAContract).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE; exit 75 = machinery,
# a tool or a canonical checkout absent (standing UNKNOWN); exit 1 carries typed REFUSED[<code>] lines
# naming the counterexample; any other exit = the court ran and witnessed nothing (standing UNKNOWN).
# Machinery (step CE23-12): release/v26.9.23/courts/ce23_12/court.py msa. MSA = Repeatability_verifier
# AND Reproducibility_environment AND MutationSensitivity AND ClassificationAgreement: the MSA contract
# is defined (C0 C1: every operator MSA question maps to an MSA property covered by a court with a
# status for today; executor MSA_ALIVE is successor work and never claimed) and the benchmark design's
# own measurement system is measured on every run, each question with (n, defects, exact 95% upper
# bound, tier): Q1 repeatability, Q2 classification agreement of five instruments over three independent
# law encodings (Cohen's kappa; the three SPARQL-text engines count as one encoding), Q3 mutation
# sensitivity (every unit a distinct corrupted subject judged on the mutant by the instrument that guards
# it and witnessed informative by a blinded variant of it), Q4 stale-receipt detection, Q5 ordering
# invariance, Q6 environment / cached-state reproducibility, Q7 the near-miss vs KNOWN membership
# boundary; then the anti-vacuity corpus. Pins: ce23_12/pins.toml; mutants: ce23_12/mutations.toml.
here=$(cd "$(dirname "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "UNKNOWN[TOOL_MISSING] CE23-12-MSAContract: python3 not on PATH"; exit 75; }
[ -f "$here/ce23_12/court.py" ] || { echo "UNKNOWN[MACHINERY_ABSENT] CE23-12-MSAContract: $here/ce23_12/court.py"; exit 75; }
PYTHONDONTWRITEBYTECODE=1 exec python3 "$here/ce23_12/court.py" msa "$@"
