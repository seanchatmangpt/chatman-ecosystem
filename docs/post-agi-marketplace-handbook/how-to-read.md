# How to Read This Book

This book can be read linearly, but its deeper structure is a graph.

## If you are building a marketplace integration now

Read Parts I–IV, then jump to the vendor chapter for your first target. Do not start by copying the vendor's sample handler. First create the canonical product, agreement, entitlement, fulfillment, usage, and receipt objects. The adapter should be the last semantic layer, not the first.

## If you are preparing for Fortune 5 procurement

Read Parts V and VI after Chapters 5–15. The commercial control plane matters because security, legal, support, and procurement evidence must join to exact product and agreement identities.

## If you are building the manufacturing system

Read Parts VII–IX. The critical correspondence is:

```text
graph → query → ggen → generated projection
      → admission → runtime qualification
      → BRCE → receipt → replay → standing
```

Generated artifacts are replaceable views. The admitted graph and qualified evidence are the durable assets.

## If you are building agentic operations

Read Parts VIII–XI. Gym execution is not production authority; a planner is not a policy; a policy is not an authority grant; a hook manufactures an intent rather than actuating it.

## Status vocabulary

Use these types consistently:

- `UNKNOWN` — evidence is absent or insufficient.
- `PARTIAL_ALIVE` — a bounded subset executed and verified.
- `ALIVE` — the exact admitted subject executed against the required verifier with receipt/replay evidence.
- `BLOCKED` — a known external or prerequisite boundary prevents the next transition.
- `BUILD_BROKEN` — the candidate cannot currently build or validate.
- `UNSUPPORTED` — the bounded system does not implement the requested capability.
- `REFUSED:*` — the request was understood but rejected by an explicit rule.

A checkpoint is not a crown. A marketplace listing is not a completed transaction. Inspection is not execution.

## The three authority classes

**SELECT** chooses among admitted candidates.

**CONSTRUCT** creates reversible artifacts and intents.

**DO** creates consequential external state.

You should be able to point to the exact transition where a chapter crosses from construction into DO. If you cannot, the architecture is not finished.

## Exercises

Each chapter ends with an operational exercise. The requested output is always evidence-bearing: exact subject, assumptions, typed gaps, verification, and next falsifier. The exercise is designed to become a reusable marketplace pack or qualification fixture rather than disposable homework.
