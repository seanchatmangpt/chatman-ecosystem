# Weaver × Ash.Reactor

This adapter makes the Chatman Ecosystem Weaver verification rail a first-class
Ash surface without allowing Ash to own constitutional identity, authority,
standing, or receipts.

## Execution graph

`WeaverAsh.Control.crown` is a generic Ash action whose implementation is
`WeaverAsh.CrownReactor`.

The Reactor performs:

1. exact-subject admission through `WeaverAsh.Capability.admit_subject`;
2. the complete existing Weaver capability matrix through
   `WeaverAsh.Capability.run_matrix`;
3. an additional native Ash stdin `weaver registry live-check`;
4. an additional native Ash OTLP live-check plus loopback emit, gated by
   exact-subject broker evidence;
5. receipt replacement/finalization so the canonical live-check capabilities
   are the Ash/Reactor executions, not the compatibility-shell observations.

The existing shell matrix remains a compatibility provider. It is not the
workflow crown once this adapter is active.

## Run

From this directory:

    mix deps.get
    mix compile --warnings-as-errors
    mix test

Then, from an exact repository checkout:

    ECOSYSTEM_SUBJECT_SHA="$(git rev-parse HEAD)" \
    WEAVER_DO_AUTHORITY_SUBJECT="$(git rev-parse HEAD)" \
    WEAVER_DO_AUTHORITY_SCOPE="weaver.loopback" \
    mix weaver.crown --root ../..

`weaver.loopback` is intentionally the only admitted DO scope. A different
subject or scope is a typed refusal. The CI workflow supplies that bounded
authority evidence only for its ephemeral local OTLP receiver.

## Standing

Compilation, action introspection, or compatibility-shell success is not the
crown. `ALIVE` requires the exact-head workflow to execute the Ash action,
Reactor graph, native stdin live-check, native OTLP live-check, receipt
finalization, and integrity hash successfully.
