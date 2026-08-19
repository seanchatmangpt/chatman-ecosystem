# ce-authority/1 — Authority as a Supplied Object, Not an Intrinsic Property

> Status: draft, fragment 1 of the `ce-*` protocol family proposed in the DfCM inversion
> (2026-08-19). Independently versioned per the inversion's own stated goal: an implementation
> may satisfy `ce-authority/1` without satisfying any other `ce-*` fragment.

## The claim this fragment formalizes

> No capability possesses authority. Authority is an independently supplied object that
> constrains which morphisms may complete.

Formally: `Capability → Authority` (today's graph) inverts to `Authority → admissible Capability`.
`SELECT(x)` gains no authority from being planned; `CONSTRUCT(x)` gains no authority from being
manufactured; `DO(x)` exists only when an external `Authority` object admits that exact
consequence.

## Checked against this repository's real code (2026-08-19) — where the claim already holds, and where it does not

This fragment is written from a real, mixed finding, not from the premise alone.

### Where `Capability → Authority` still holds (the un-inverted case)

`platform-console/app/lib/castle.ts`'s `resolveCastleVerb(verbId)` returns an admitted verb
purely by static membership in `ALLOWED_CASTLE_VERBS`, a compile-time table. There is no
separate object consulted at call time that could, independently of this table, refuse a verb
the table admits or admit one it doesn't. The capability's definition and its authority are the
same artifact. This is exactly the graph the inversion names as the thing to invert — confirmed
by reading the code, not assumed from its docstring.

### Where `Authority → admissible Capability` already, partially, holds

Two real objects in this codebase already behave as externally-supplied authority, separate from
capability definition:

- `platform-console/app/lib/freeze-windows.ts`'s `checkFreezeGuard(orgId, actor)` — consulted
  by `castle.ts`'s `runCastleVerb`, `api/orgs/[id]/tier/route.ts`, and
  `api/projects/[name]/{tier,quota}/route.ts` *before* their respective `DO`s complete. It can
  refuse a `DO` those routes' own code would otherwise permit, based on state (an active
  `FreezeWindow`) that has nothing to do with the capability's own definition.
- `platform-console/app/lib/approval-workflow.ts`'s `requireApproval(action, targetId,
  resourcePayload)` — a maker-checker object, independently persisted, that gates completion of
  `org.delete`, `quota.override`, `tier.downgrade`, `sla.credit.apply`, `dsar.erasure`,
  `freeze.override`, and `backup.retention.change`. The approving identity must differ from the
  requesting identity — checked in code, not merely documented — which is exactly the shape of
  an authority object independent of the capability being authorized.

Both are real, shipped, exercised-in-production-shaped code (this session verified
`freeze-windows.ts`'s guard live against Castle's verb execution and `approval-workflow.ts`'s
self-approval refusal via `tsc`-checked logic paths). Neither is universal — they gate specific,
named actions, not every `DO` in the system.

## What `ce-authority/1` conformance actually requires

An implementation conforms to `ce-authority/1` if and only if:

1. Every `DO(x)` in the implementation is preceded by a call to an `AuthorityObject.admits(x):
   boolean` (or equivalent) whose implementation is not the same code artifact that defines the
   capability being checked.
2. The `AuthorityObject` can be swapped (a different org, a different policy, a different
   deployment) without recompiling or redefining the capability set itself.
3. A capability's own definition contains no embedded admissibility decision — `resolveCastleVerb`-
   shaped functions, where membership-in-table equals admission, do not conform.
4. Refusal by the `AuthorityObject` is itself a receiptable event (this connects to
   `ce-receipt/1`, a separate fragment — `ce-authority/1` alone does not require receipting,
   only that refusal be possible and observable).

## Real, scoped gap this repository has today against its own proposed fragment

**Update (2026-08-19): partially closed for one call site.** A real `AuthorityObject` interface
now exists — `platform-console/app/lib/authority-object.ts` — exporting `AuthorityConsequence`,
`AuthorityDecision`, the `AuthorityObject` interface (`admits(consequence): Promise<AuthorityDecision>`),
and `DefaultAuthorityObject`, which composes `freeze-windows.ts`'s `checkFreezeGuard` (always
consulted) and `approval-workflow.ts`'s `requireApproval` (consulted only for the closed
`ACTIONS_REQUIRING_APPROVAL` set). `platform-console/app/lib/castle.ts`'s `runCastleVerb` now
calls `defaultAuthorityObject.admits({kind:"castle.verb.run", ...})` after its existing
structured freeze check and before building/POSTing the k8s Job manifest. `npx tsc --noEmit`
from `platform-console/app` is clean.

This closes conformance requirement 1 (a call to an `AuthorityObject.admits()` not defined by the
same artifact as the capability) for exactly one call site: `runCastleVerb`. It does **not**
close requirement 3: `resolveCastleVerb` itself — the table-membership admission check inside
`runCastleVerb` — is untouched; capability resolution and authority admission are now two
separate, composable checks on this one path, but the table-intrinsic admission still exists
alongside the new object, it has not been replaced by it. The 12 actions already routed through
`approval-workflow.ts`'s `requireApproval` directly (`org.delete`, `quota.override`,
`tier.downgrade`, `backup.retention.change`, `export-subscription.update`, `dr.failover`,
`dsar.erasure`, `castle.verb.schedule`, `freeze.override`, `environment.promote`,
`deployment.quarantine`, `sla.credit.apply`) still call `requireApproval` at their own call
sites, not through `AuthorityObject.admits()` — they remain in the "gated by table/direct-call,
not by the uniform object" tier this fragment named as the gap. The two-tier situation described
above is now a *three*-tier situation: (a) `runCastleVerb`, gated by both `resolveCastleVerb`
table membership and the new `AuthorityObject`; (b) the 12 approval-gated actions, gated by
direct `requireApproval`/`checkFreezeGuard` calls, not yet migrated to the object; (c) any other
mutating call site in the app, gated by neither. Migrating (b) and (c) onto
`AuthorityObject.admits()` as the single uniform check remains a real, scoped, buildable item —
not started.

## Explicit non-claims

- This fragment does not claim `platform-console` as a whole conforms to `ce-authority/1` today.
  It conforms partially, for 7 named actions plus Castle verb execution's outer guard, and does
  not conform for capability admission itself.
- This fragment does not claim any party outside this repository has implemented or reviewed
  `ce-authority/1`. It is a draft, versioned as `1` because it is the first attempt, not because
  it has been ratified.
