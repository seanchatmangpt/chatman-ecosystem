# Why Replicated Evidence Stops at PARTIAL_ALIVE

**Diátaxis role:** Explanation. This page explains the design boundary; factual API details live in [Reference](../reference/replicated-evidence-state.md).

Replicated observations solve an epistemic problem before they solve an actuation problem. The capsule asks whether a bounded set of replica states is sufficiently consistent, fresh, and agreeing to manufacture a replayable local qualification. It deliberately does not turn that qualification into consequential authority.

## Local convergence is not a Crown

A strict-majority winner can establish useful evidence about one exact subject, but repository `ALIVE` requires more: positive and negative behavior, integration, exact-head verification, persisted evidence, receipt integrity, replay, exclusions, drift checks, and common subject identity across all required rails. The engine therefore emits `PARTIAL_ALIVE`, never `ALIVE`.

This is a non-collapse rule:

```text
replica agreement != repository Crown
receipt exists != consequential authority
CONSTRUCT != DO
UNKNOWN != ADMITTED
```

## Why split brain becomes UNKNOWN

At the highest observed generation, two different value digests mean the bounded observations cannot establish one current value. Flattening that disagreement would manufacture certainty. The engine preserves the conflict as topology and returns `UNKNOWN` with no receipt.

## Why the lease is half-open

The lease admits `not_before <= now < expires_at`. Excluding the expiry instant avoids two adjacent validity windows both claiming the same boundary moment. A stale lease is refused before quorum evidence is interpreted as current.

## Why the Merkle root is order-independent

Replica digests are sorted before reduction. Input order therefore cannot change the evidence root. The receipt binds the winning subject, generation, value digest, root, standing, and explicit `actuation_performed=False` into canonical JSON before hashing.

## Why DO is refused early

`admit_action` runs before lease/conflict/quorum work. `ActionClass.DO` raises `REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]`. This preserves the repository constitution: access to a qualification engine is not authority to mutate an external system, and consequential changes belong behind BRCE with their own receipt/replay contract.

## DfCM boundary

The engine preserves lawful possibilities instead of collapsing them prematurely:

- older generations remain observable while only the maximum generation participates in conflict classification;
- concurrent vector clocks remain representable;
- split-brain values remain explicit rather than guessed away;
- minority evidence remains `UNKNOWN` rather than being promoted;
- local qualification remains separate from consequential action.

The result is intentionally narrower than distributed consensus. That exclusion makes the capsule auditable: deterministic evidence qualification can be proven independently of network timing, leader election, or external side effects.
