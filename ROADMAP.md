# ROADMAP.md

## Objective

Manufacture the first four working systems for the Rust agent fabric without
recreating the unresolved aggregate surfaces of the source repositories.

## Gall checkpoint matrix

| Checkpoint | Roadmap phase | Consequence | Positive fixture | Negative fixture | Crown command |
|---|---:|---|---|---|---|
| GALL-S0 | 0 | exact capability graph admitted | 9 pinned sources, one BRCE owner | duplicate source and authority multiplicity | `cargo run --bin gall -- --json` |
| GALL-S1 | 1 | canonical action actuated and replayed | admitted echo | mutated action and undeclared capability | same |
| GALL-S2 | 2 | four channels route through one gateway | CLI/WebChat/Telegram/Discord echo | unknown subject, revocation, prompt authority injection | same |
| GALL-S3 | 3 | real WASM import actuates only through BRCE | `(i32)->i32` skill | import, digest and fuel refusals | same |

## Phase 0 — ALIVE criteria

- Exact source coordinates are data, not prose.
- Roles are explicit.
- Exactly one repository owns actuation.
- A malformed graph cannot receive admission.

## Phase 1 — ALIVE criteria

- The approved action object is byte-identical to the executed action.
- Every broker attempt emits a verifiable receipt.
- Replay enters through a broker seeded by the recorded predecessor.
- No public function can call the private actuation kernel directly.

## Phase 2 — ALIVE criteria

- Presentation channels do not own policy or actuation.
- Channel identity is mapped before intent construction.
- Revocation changes subsequent admission.
- Untrusted text remains an argument and cannot mutate policy.

## Phase 3 — ALIVE criteria

- Module bytes are valid WebAssembly.
- Module identity is immutable and verified before parsing.
- Imports are an allowlisted manifest set.
- The only supported host import constructs a canonical action and submits it
  to BRCE.
- Fuel is finite.
- Every refusal is typed and receipted.

## Immediate extension fence

Do not add live provider, network channel, marketplace, native client, arbitrary
WASI, dynamic credential, or distributed workflow support until GALL-S0 through
GALL-S3 execute at the exact candidate head.

## Falsifiers

The four-phase crown is invalidated by any observation that:

1. permits actuation outside `Broker::actuate`;
2. allows a changed action to reuse an admission token;
3. produces a broker outcome without a valid receipt;
4. lets channel content modify policy;
5. permits an undeclared WASM import;
6. executes bytes whose digest differs from the manifest;
7. reports a later checkpoint after an earlier checkpoint failed;
8. cannot reproduce the exact crown with the documented commands.
