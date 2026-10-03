# Loops of Loops — Implementation Receipt (v26.10.2)

Implementation receipt for the v26.10.2 closed manufacture loop: five lanes (L1–L5)
landing the `loops-of-loops.md` invariants across seven repositories, plus this
documentation lane (L6). Spec-side traceability table:
[loops-of-loops.md §8](loops-of-loops.md).

## 1. Subject identity

- **Repository:** `chatman-ecosystem` (this receipt)
- **Branch:** `docs/v27927-closed-manufacture-loop`
- **Base SHA:** `b3416dfd` (the branch carried the spec `docs/architecture/loops-of-loops.md`)
- **Loop:** v26.10.2 closed manufacture loop, lane L6 (spec traceability + receipt)
- **Lane ownership:** L6 edits only
  `docs/architecture/loops-of-loops.md` and adds
  `docs/architecture/loops-of-loops-implementation.md`; all other repos read-only.

## 2. Per-lane receipts

| Lane | Repo(s) @ SHA | Landed files | Falsifiers / courts run | Standing |
|---|---|---|---|---|
| L1 | `ash_a2a@7b36935` | `lib/ash_a2a/authority/lease.ex`, `lib/ash_a2a/authority/two_port_gate.ex`, `lib/ash_a2a/chicago/courts/two_port_gate.ex`, `lib/ash_a2a/chicago/mutation/catalog.ex`, `lib/ash_a2a/command_bus.ex`, `priv/sa2a/chicago_court_manifest.json`, `test/ash_a2a_two_port_gate_test.exs` | CHI-TWO-PORT court + 4 mutants (catalog); `test/ash_a2a_two_port_gate_test.exs` | ALIVE — Ed25519 sign/verify; hybrid clock (wall-clock persisted validity + same-VM monotonic admission window); 4-bit null mask, all conjuncts evaluated unconditionally; CommandBus opt-in `check_lease_gate`; 106 µs median admission (≤10 ms budget, ~100× headroom) |
| L2 | `ash_r2rml@0d5320f` | `lib/ash_r2rml/delta.ex`, `lib/ash_r2rml/obda_in_memory.ex` (`materialize_many opts[:previous_graph]`), `test/delta_budget_test.exs` | `test/delta_budget_test.exs` | ALIVE — `Delta.diff/2` + `root_digest` (SHA-256 over sorted canonical N-Triples, self-describing prefix); 100-row tier 1.5/4.5 ms (≤20 ms budget); zero-copy disclosure carried honestly (§4.1) |
| L3 | `ggen_igniter@72afe77` | `lib/ggen_igniter/semantic_jira/transition_log.ex`, `.../reconciler.ex`, `.../prov_events.ex`, `test/ggen_igniter_semantic_jira_transition_log_concurrency_test.exs`, `..._reconciler_test.exs`, `..._prov_events_test.exs` | TransitionLog concurrency court, Reconciler + prov_events tests | ALIVE — epoch `e` (u64 ledger-generation, marker-persisted, regression refused typed); `vc_dominates?`/`vc_concurrent?` weak order; Reconciler refuses `{:vc_concurrent, incoming, last}` before any byte; `prov_events` project `sj:epoch` + `sj:vectorClock` conditionally |
| L4 | `xaas@9cda677a` + `ash_pplan@af65623` | xaas: `lib/xaas/ultracode/{andon,andon_supervisor,convergence_receipt}.ex`, `.../semantic_crown.ex`, `.../semantic_drive.ex`, `.../semantic_drive/ocel.ex`, `lib/xaas/application.ex`, `test/xaas/ultracode/{convergence_receipt,semantic_crown}_test.exs`. ash_pplan: `lib/ash_pplan/fond/{policy_supervisor,policy_switch,recovery}.ex`, `test/fond/horizon_test.exs` | `convergence_receipt_test.exs` (receipt at exactly k_max, one Andon trip), `semantic_crown_test.exs`, `test/fond/horizon_test.exs` | ALIVE — `ConvergenceReceipt` (FAILED_CONVERGENCE class, `horizon_witness` sha256, standing `BLOCKED:epistemic_horizon_exceeded`); crown `opts[:k_max]` default 2, drive `opts[:k_max]` default `nil` (= today's unbounded); Andon cord ETS GenServer, opt-in `:andon_enabled`; PolicySupervisor horizon default 9 + `horizon_exceeded?/1` + recovery route |
| L5 | `ggen_igniter@d82e0f1` | `lib/ggen_igniter/semantic_jira/sovereign_lease.ex`, `.../semantic_jira.ex`, `.../bootstrap/receipts.ex`, `.../r_projection.ex`, `lib/mix/tasks/semantic_jira.admit_candidates.ex`, `priv/ggen/semantic-jira-pack/gates/066_monotonic_evolution.rq`, `priv/ggen/semantic-jira-pack/ontology.ttl`, `priv/schema/refusals.schema.json`, `docs/reference/refusals.md`, `test/ggen_igniter_semantic_jira_sovereign_lease_test.exs`, `test/..._admit_candidates_sovereign_test.exs` | Sovereign lease court; `admit_candidates` sovereign tests; gate `066_monotonic_evolution` | ALIVE — SovereignLease ≥2 distinct Ed25519 signers over canonical bytes; `shape_digest_unchanged` refusal (evolution requires a real digest delta); no wall clock in admit; `"SOVEREIGN"` requirement literal + `--sovereign-keys`; registry 132→135 |
| (en route) | `ggen_igniter@0789e42` | `lib/ggen_igniter/semantic_jira/cli.ex`, `.../descriptor.ex`, `lib/mix/tasks/semantic_jira.xaas_receipt.ex`, `test/..._semantic_jira_descriptor_test.exs` | descriptor test | ALIVE — `receipt_from_xaas/3` `required_evidence` threading; the F6 promotion-refusal fix |
| L6 | `chatman-ecosystem` @ this commit | `docs/architecture/loops-of-loops.md` (§8 + Level-3 diagram mapping), `docs/architecture/loops-of-loops-implementation.md` (this file) | this receipt | ALIVE — traceability table of 13 rows against the spec §1.1–§1.3 invariants; every repo@SHA cited above re-verified on the local checkouts this session |

## 3. Cross-lane verification results

1. **L1 null-mask semantics.** `TwoPortGate.evaluate/3` refused/admitted exactly per
   mask semantics: each of scope (`0x1`), RDFC10 root (`0x2`), clock (`0x4`),
   signature (`0x8`) independently drives its conjunct to refusal while the other
   three conjuncts are still evaluated — the branchless property the spec requires
   (§1.1 "branchless null-mask"). Witnessed by CHI-TWO-PORT plus the 4-mutant
   catalog, and asserted in `test/ash_a2a_two_port_gate_test.exs`.
2. **L4 receipt at exactly k_max with one Andon trip.** The convergence court drives
   the loop to exactly `k_max` and asserts: the FAILED_CONVERGENCE receipt exists
   (with `horizon_witness` sha256), Andon recorded exactly one trip, and the loop
   self-halts. `drive` without `k_max` remains unbounded (today's behavior), so the
   bounded horizon is opt-in per crown/drive invocation.
3. **L5 loosening-refused / tightening-passed.** The monotonic-evolution court
   refuses an evolution attempt whose shape digest is unchanged
   (`shape_digest_unchanged`), refuses signature loosening, and admits
   constraint-tightening. Gate `066_monotonic_evolution.rq` encodes the same
   refusal at the pack layer; `admit_candidates` carries the `"SOVEREIGN"`
   requirement literal and `--sovereign-keys`.

## 4. Disclosed deviations

1. **Zero-copy slicing.** The spec's "zero-copy vector slicing" (§1.1) is not
   shippable on wasmex 0.15.1 (no memory-view API). Honest v1 = digest contract +
   measured copy cost inside the ≤20 ms budget; upgrade path: dedicated NIF or
   direct wasmtime host access.
2. **Blake3 → SHA-256.** The spec already hedges "Blake3/SHA-256" (§1.1). Survey:
   zero Blake3 anywhere in the fleet; SHA-256 over sorted canonical N-Triples with a
   self-describing prefix landed instead (L2 `root_digest`, L4 `horizon_witness`).
3. **Andon scoping.** The spec's "trip the OTP supervisor tree" (§1.2) is satisfied
   by a recorded ETS cord (opt-in `:andon_enabled`) plus loop self-halt, not a
   restart cascade. A restart cascade is a production-topology decision, deferred
   with `AndonSupervisor` present for that topology.
4. **`BLOCKED:` spelling.** The spec's parenthetical spelling of the horizon standing
   was falsified against the real fleet refusal regex; the landed standing is
   `BLOCKED:epistemic_horizon_exceeded` and the spec text around it was written to
   match the fleet.
5. **Clock hybrid.** The spec's pure-monotonic clock discipline (§1.1) landed as a
   hybrid law in `Authority.Lease`: wall-clock persisted validity (what the lease
   certifies across VMs) + same-VM monotonic admission window (spoof-proof inside
   the admission loop). Wall-clock spoofing cannot move the admission window.
6. **SOVEREIGN at ceiling DO.** The fleet refusal schema's ceiling enum is closed;
   SOVEREIGN projects at ceiling DO, documented at three sites (refusals schema,
   `docs/reference/refusals.md`, pack ontology).

## 5. Honest gaps and residues

- **Zero-copy slicing** — see §4.1; the only spec capability not landed as
  specified, disclosed with an upgrade path.
- **1.17 floor leg** — not landed in this loop; carried as an open leg.
- **Known residues (pre-existing, unchanged by this loop):** strict-profile STOP in
  ggen; SA2A-TOPO-002 user configuration.

## 6. Replay commands

Each repo replays from its canonical checkout at the exact SHA. All commands are
`mix` gates; run from the repo root.

```bash
# L1 — ash_a2a @ 7b36935
git -C ~/ash_a2a checkout 7b36935
cd ~/ash_a2a && mix deps.get && mix compile
mix test test/ash_a2a_two_port_gate_test.exs
mix ash_a2a.chicago            # CHI-TWO-PORT court
mix ash_a2a.chicago.mutate     # 4-mutant kill check

# L2 — ash_r2rml @ 0d5320f
git -C ~/ash_r2rml checkout 0d5320f
cd ~/ash_r2rml && mix deps.get && mix compile
mix test test/delta_budget_test.exs

# L3 — ggen_igniter @ 72afe77
git -C ~/ggen_igniter checkout 72afe77
cd ~/ggen_igniter && mix deps.get && mix compile
mix test test/ggen_igniter_semantic_jira_transition_log_concurrency_test.exs \
         test/ggen_igniter_semantic_jira_reconciler_test.exs \
         test/ggen_igniter_semantic_jira_prov_events_test.exs

# L4 — xaas @ 9cda677a + ash_pplan @ af65623
git -C ~/xaas checkout 9cda677a
cd ~/xaas && mix deps.get && mix compile
mix test test/xaas/ultracode/convergence_receipt_test.exs \
         test/xaas/ultracode/semantic_crown_test.exs
git -C ~/ash_pplan checkout af65623
cd ~/ash_pplan && mix deps.get && mix compile
mix test test/fond/horizon_test.exs

# L5 — ggen_igniter @ d82e0f1
git -C ~/ggen_igniter checkout d82e0f1
cd ~/ggen_igniter && mix deps.get && mix compile
mix test test/ggen_igniter_semantic_jira_sovereign_lease_test.exs \
         test/ggen_igniter_semantic_jira_admit_candidates_sovereign_test.exs

# F6 fix — ggen_igniter @ 0789e42
git -C ~/ggen_igniter checkout 0789e42
cd ~/ggen_igniter && mix deps.get && mix compile
mix test test/ggen_igniter_semantic_jira_descriptor_test.exs

# L6 — chatman-ecosystem @ this branch head
git -C ~/chatman-ecosystem checkout docs/v27927-closed-manufacture-loop
test -f docs/architecture/loops-of-loops-implementation.md && echo L6-ALIVE
```

## 7. Standing summary

| Plane | Standing | Basis |
|---|---|---|
| L1 two-port gate + leases (ash_a2a) | ALIVE | court + mutants + measured 106 µs on exact subject `7b36935` |
| L2 differential projection (ash_r2rml) | ALIVE | budget court on exact subject `0d5320f`; zero-copy leg disclosed |
| L3 epochs + vector clocks (ggen_igniter) | ALIVE | concurrency court on exact subject `72afe77` |
| L4 horizon + Andon (xaas + ash_pplan) | ALIVE | convergence court on exact subjects `9cda677a`/`af65623` |
| L5 sovereign ceiling (ggen_igniter) | ALIVE | sovereign court on exact subject `d82e0f1` |
| F6 evidence threading (ggen_igniter) | ALIVE | descriptor test on exact subject `0789e42` |
| L6 traceability + receipt (this repo) | ALIVE | this receipt; 13-row traceability vs spec §1.1–§1.3 |
| Zero-copy slicing | PARTIAL_ALIVE | digest contract + measured copy cost; memory-view upgrade path named |
| 1.17 floor leg | UNKNOWN | not landed in this loop |
