# 62. Autonomous Marketplace Operations

## Closed loop without collapsed types

Autonomous marketplace operations can observe failures, diagnose them, construct repairs, qualify candidates, and execute bounded remedies. Autonomy is safe only when observation, construction, admission, authority, actuation, receipt, and standing remain separate types.

```text
Observe
→ Diagnose
→ Construct
→ Admit
→ DO
→ Verify
→ Receipt
→ Replay
→ Standing
```

The speed of the loop can approach machine time. Its authority boundaries remain explicit.

## Example: rejected meter batch

Observation: a marketplace rejects a frozen batch for an invalid dimension.

Diagnosis: the canonical meter is valid, but the projection used a deprecated vendor dimension ID.

Construction: generate a corrected mapping and a new submission intent referencing the same underlying usage batch according to the vendor's correction rules.

Admission: confirm the vendor contract/version, exact agreement/window, idempotency behavior, and that a second charge cannot occur.

DO: broker the corrective submission.

Verification: observe vendor acceptance and reconcile quantity.

Receipt/replay: bind old failure, corrected projection, authority, external IDs, and postcondition.

The loop can be automatic when every edge is proven safe.

## Ambiguous result stops the loop

If the original meter call timed out after possible acceptance and the vendor provides no reliable idempotency/read path, the correct autonomous action may be **none**. Escalate with evidence.

Autonomy is not measured by how rarely a human is involved. It is measured by how much lawful work closes without sacrificing evidence or authority.

## Repair budgets

Define limits for retries, spend, customer scope, resource count, time, marketplace account, and consequence class. An agent that exceeds the budget transitions to BLOCKED rather than expanding its own authority.

## Learning

Counterexamples can improve planners, templates, fixtures, and policies through admitted updates. A runtime agent must not modify the policy that governs its own authority as an incidental learning action.

## Standing updates

The standing calculator consumes receipts. It can promote a bounded capability after required execution and verification. It cannot promote a broader market or version than the evidence subject.

## Refusals

- `REFUSED:AMBIGUOUS_FINANCIAL_AUTORETRY`
- `REFUSED:SELF_EXPANDING_REPAIR_BUDGET`
- `REFUSED:AGENT_EDITS_OWN_AUTHORITY_POLICY`
- `REFUSED:STANDING_BEFORE_VERIFIED_POSTCONDITION`
- `REFUSED:LOCAL_REPAIR_AS_GLOBAL_ALIVE`

## Operational exercise

Design autonomous loops for rejected meter, stale entitlement callback, failed Kubernetes fulfillment, and listing drift. Identify the branch where each loop must stop because consequence or authority is ambiguous. Encode that stop as a first-class refusal, not a human-only convention.
