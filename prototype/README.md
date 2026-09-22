# prototype/ — SCM vertical slice

A runnable vertical slice of the Chatman Semantic Coordination Machine (SCM):
pure **composition** operators, a machine-enforced **jurisdiction** registry, a
**conservation verifier** for the calculus invariants, and **one semantic
compound** carried through the full lawful projection chain

```
Ontology -> HDDL/FOND -> Ash -> A2A -> DO boundary -> OCEL/Receipt
```

All vocabulary is reused verbatim from the 20 Sigma classes at
`packs/scm-sigma-pack/ontology.ttl`. Enforced invariants: SELECT is not
CONSTRUCT is not DO; PlannerOutput is not Authority; DO requires a Receipt; new
Authority requires an explicit Grant, Delegation, or Rule. Every module is pure
stdlib Python (dicts in, dicts out) — no framework, no I/O, no mocks in tests.

## Module map

| Module | What it does |
|---|---|
| `composition.py` | Pure SELECT/CONSTRUCT-shaped operators over typed dicts: `aggregate`, `compose_heterogeneous`, `sequence`, `project`, `admit`, and `admit_all` (admission with stop-at-first-refusal). Never acts, never produces a Receipt, never grants Authority. |
| `compound.py` | The one semantic compound: a role-relative Continuation projected hop-by-hop (`canonical_compound` → `project_to_hdld` → `project_to_ash` → `project_to_a2a` → `project_to_do_boundary` → `project_to_receipt`) plus `check_preserved_properties` (principal/artifactId/timestamp survive every hop; role survives through the ash hop). Authority is acquired only at the a2a hop; the Receipt digest is computed, never asserted. |
| `jurisdiction.py` | Enforced registry mapping each repo/component to the Sigma Z-coordinates it may touch (`JURISDICTION_TABLE`, the AGENTS.md "Owns" column) and the capabilities it must not own (`MUST_NOT_OWN`, the "Must not own" column). `check_jurisdiction`, `check_forbidden` (fail-closed on unknown components), and the `guard` decorator raise `JurisdictionViolation` outside contract. |
| `verifier.py` | `ConservationVerifier` — runtime conservation checks over Z = (P, Γ, Ω, B, τ, J, Authority, Receipts): DO-requires-Receipt, authority-grant, planner-output-is-not-authority, receipt-digest-recomputation, permit-required-for-actuation, no-self-certification; `verify_transition` collects all violations before raising. |
| `demo.py` | Pure-print walkthrough of the full chain plus three refusal demos (bad `grantedBy`, out-of-jurisdiction coordinate, missing `permitRef`); exits 0 only if all properties are preserved and all three refusals actually raise. No writes. |
| `tests/conftest.py` | Puts `prototype/` on `sys.path` so tests import the sibling modules with no install step. |
| `tests/test_composition.py` | State-based tests for the composition operators (associativity, non-commutativity, order preservation, idempotence, admission truthiness). No mocks. |
| `tests/test_pipeline.py` | State-based tests for the full hop chain end-to-end, the jurisdiction registry, and every verifier check, including `admit_all` stop-at-first-refusal. No mocks. |
| `tests/test_jurisdiction_contracts.py` | PR-3 slice: parses the `## Jurisdiction table` in the repo-root `AGENTS.md` and refuses doc/code drift — the registry must match the constitution's table exactly (13 repos, Owns and Must-not-own columns), and every must-not-own capability must produce a real `REFUSED_JURISDICTION_FORBIDDEN`. |

## Ported cross-repo patterns (commit c028968)

Three real patterns, ported from cross-repo reconnaissance rather than invented
(reuse-before-invention discipline):

1. **`admit_all` with stop-at-first-refusal** — from **praxis-graphlaw**
   (`crates/praxis-graphlaw/src/chatman/admission8.rs:243`; the
   stop-at-first-refusal behavior is proven by that file's own test
   `admit_all_stops_at_first_refusal`, line 428). Ported as
   `composition.admit_all`; returns `(admitted_list, refused_at_index)`.
2. **Receipt digest computed from canonical material, never asserted** — from
   **praxis-graphlaw** `Receipt::from_canonical_nquads`
   (`crates/praxis-graphlaw/src/chatman/abi.rs:217-260`). Ported as
   `verifier.compute_receipt_digest` / `check_receipt_digest` (sha256 over the
   sorted canonical fields, stdlib hashlib since blake3 is not stdlib), applied
   in `compound.project_to_receipt`.
3. **Permit-gated actuation** — from **mfw**'s
   `InvocationEnvelope::admit()`/Admission (`runtime/mfw-rmcp/src/admission.rs:19-48`),
   where actuation is gated on a signed `PermitPayload`, not a bare `grantedBy`
   label. Ported as `verifier.check_permit_required_for_actuation` plus the
   `permitRef` field threading through `project_to_a2a` →
   `project_to_do_boundary`. The same mfw port chains receipts via
   `predecessorReceiptHashes` (`mfw-meaning/src/receipt.rs:109-128`;
   `runtime/mfw-rmcp/src/admission.rs:34-48`).

## Running the tests

From the repo root (`~/chatman-ecosystem`):

```
python3 -m pytest prototype/tests -q
```

Observed 2026-09-21 at main @7ac66d8, tree uncommitted/clean: **28 passed,
exit code 0** (`python3.13 -m pytest prototype/tests -q` → `28 passed in
0.07s`, exit 0). No code was modified to obtain this result.

Note: the bare `python3` on this machine (Xcode CLT python, 3.9) has no pytest
(`No module named pytest`, exit 1); any interpreter with pytest installed works
(e.g. `python3.13`, `python3.12`, `python3.11`), because `conftest.py` needs no
package installation.

The demo is side-effect-free (pure print + exit code):

```
python3.13 prototype/demo.py   # exit 0 observed 2026-09-21: 4/4 properties preserved, 3/3 refusals raised
```

## Status

- Test suite: **ALIVE** as observed 2026-09-21 (28/28 passed, exit 0, exact
  commands above). Matches the prior known-good run at merge 7ac66d8 on
  2026-09-19 — no divergence.
- Demo: **ALIVE** as observed 2026-09-21 (exit 0).
- Everything else in this document is inspection-only (file reads), not
  observed execution.

## Repo context

This is a local-only repository (no git remotes), `main` @7ac66d8; the GitHub
repo of the same name is unrelated.
