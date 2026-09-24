# Imported-crown fixture sources

Each `<name>-receipts/` directory is a stop-court receipt directory (one STOP receipt and the
gate receipts of checkpoint GC-26.9.23) plus `XAAS_SHA` and `GI_SHA`, the exact subjects an
importer binds to the crown component (xaas) and the paired component (ggen_igniter).
`qualification/imported-crown.<name>.ttl` is `bin/import-crown-lift.py` applied to that
directory and those two SHAs; `qualify.sh` step 6 re-lifts every directory and compares bytes.

All directories are produced by `derive-fixtures.py <xaas checkout> <out>` from real git
blobs of seanchatmangpt/xaas, checked by object id before use. `XAAS_REPO=<xaas checkout>
qualification/qualify.sh` re-derives them and requires `diff -r` to be empty.

## Source blobs

| role | xaas commit : path | git blob | sha256 of the bytes |
|---|---|---|---|
| smoke STOP (counters 0) | 4b14e3f2 : receipts/v26.9.23/V23-S.gate/stop-court-STOP.receipt.json | f028286b | 303d1561634fbeb852c9fa13ca734accf775e6a90e44b640449a1abefc405951 |
| smoke gate GC23-11 | 4b14e3f2 : receipts/v26.9.23/V23-S.gate/stop-court-GC23-11.receipt.json | f787525c | f4c24d7dc38059b9e57603cfd5cfd07e19ba5681505834cc1550dcdfaed78831 |
| baseline R_0 STOP | 66b52e74 : docs/sjira/v26.9.23/receipts/STOP-GC-26.9.23.json | a9f24fa8 | 84ffe65097800c806b41bafcd3c327d20801b88dca2e2b23fc27b1cb14d19ac8 |
| baseline R_0 gates | 66b52e74 : docs/sjira/v26.9.23/receipts/GC23-{0..12}.json | (13 blobs) | verbatim in stale-r0-receipts/ |

The smoke run (V23-S, `mix xaas.stop_court --only GC23-11` at xaas 26a6a0cb with
ggen_igniter 3937a4f8) is the real source of the zero counters, the subject SHAs and the
receipt shapes. It judged only GC23-11, so STOP=false in its bytes.

## Fixtures

| fixture | XAAS_SHA | GI_SHA | content |
|---|---|---|---|
| positive | 26a6a0cb | 3937a4f8 | smoke STOP with `standing` rewritten to ALIVE ("13/13 gates ALIVE; STOP=true"); 13 gate receipts from the GC23-11 bytes with gate.gate, gate.outcome, identity.subject and standing rewritten (ALIVE). Every rewritten receipt names its source blob and rewritten fields in `qualification_rewrite`. REQUIRED_UNKNOWN keeps its real smoke value 14 (gate 090 judges only the two CE23-8 counters). |
| stale-r0 | 66b52e74 | 3937a4f8 | R_0 bytes verbatim: STOP UNKNOWN at 11a24fba "0/13 gates ALIVE; STOP=false", no release_counters, gates UNKNOWN run against ggen_igniter 5984ec48. XAAS_SHA is the commit the receipts were read from (a naive importer's binding); gate 090 refuses them at any binding. |
| llm1 | 26a6a0cb | 3937a4f8 | positive with LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH.value = 1 |
| unreceipted-null | 26a6a0cb | 3937a4f8 | positive with UNRECEIPTED_ACTUATION.value = null and a why (the court's unreadable-source form) |
| drop-gate | 26a6a0cb | 3937a4f8 | positive without GC23-12.json (12 gates) |
| foreign-subject | 26a6a0cb | 3937a4f8 | positive with GC23-7 identity.subject_sha = 11a24fba (the real R_0 subject) |
| gi-mismatch | 26a6a0cb | 3937a4f8 | positive with GC23-4 gate.ggen_igniter_sha = 5984ec48 (the real R_0 ggen_igniter subject) |

Graph-level mutants (a lift fact removed: requiredGateCount, stopReceiptSha256, the first gate
receiptSha256) are derived in scratch by `qualify.sh` from the positive lift, not committed.
