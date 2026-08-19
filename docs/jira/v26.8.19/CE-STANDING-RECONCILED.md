# ce-standing/1 — Reconciled Evidence-State Vocabulary (v26.8.19)

> Status: ratified reconciliation of two independently-evolved, real vocabularies. Supersedes
> the "real, scoped gap" noted in `docs/jira/v26.8.19/10-CE-STANDING-1.md`.

## Sources read

- `~/castle/src/v26_8_18/topology.rs:38-46` — real, shipped Rust enum `ReleaseStanding`:
  `Unknown, PartialAlive, Alive, Blocked, BuildBroken, Unsupported, Refused` (7 variants,
  `#[serde(rename_all = "SCREAMING_SNAKE_CASE")]`, each with an `as_str()` arm).
- `~/.claude/rules/no-overclaiming-rust.md` — this session's working vocabulary: `ALIVE, PARTIAL,
  BLOCKED, MOCKED, REFUSED, UNSUPPORTED, UNVERIFIED` (7 terms, prose-defined, no enum).

Both are real, in-use vocabularies (castle's is compiled and serialized; the session's is applied
throughout this session's docs). Neither is authoritative over the other — this file merges them.

## Mapping table

| castle `ReleaseStanding` | session no-overclaiming term | Relationship |
|---|---|---|
| `Unknown` | `UNVERIFIED` | Near-synonym. Both mean "no evidence checked yet, default state, never round up from here." |
| `PartialAlive` | `PARTIAL` | Direct equivalent. Some paths verified working, others not — name which paths. |
| `Alive` | `ALIVE` | Direct equivalent. Ran and passed, this session/this build. |
| `Blocked` | `BLOCKED` | Direct equivalent. A specific, citable blocker (file:line, dependency, environment) stops verification. |
| `BuildBroken` | *(no session equivalent — genuine gap, see below)* | `BuildBroken` names a compile/runtime failure of the artifact itself. Nothing in the session vocabulary names this state; `BLOCKED` is the nearest neighbor but is weaker (a blocker can exist with a healthy build). |
| `Unsupported` | `UNSUPPORTED` | Direct equivalent. By design, not attempted — not a defect. |
| `Refused` | `REFUSED` | Direct equivalent. By design, deliberately declined (e.g., a guardrail, a policy). Must be a reachable state in both vocabularies, not merely theoretical. |
| *(no castle equivalent — genuine gap, see below)* | `MOCKED` | `MOCKED` names a test-double substitution (a fake/mock/stub stood in for a real collaborator). Nothing in castle's `ReleaseStanding` names this state; it is orthogonal to build health — a mocked test can build and pass while verifying nothing real. |

## Where `BuildBroken` and `MOCKED` genuinely diverge (no false 1:1 forced)

These two terms describe **orthogonal axes**, not overlapping ones, and the reconciliation does
not collapse them:

- **`BuildBroken`** is an *artifact-health* fact: the code did not compile, or crashed at
  runtime before producing a result. It says nothing about test methodology — a build can be
  broken whether or not any test in it uses mocks.
- **`MOCKED`** is a *test-methodology* fact: a real collaborator (subprocess, file, service) was
  replaced with a fake/mock/stub for the check being reported. It says nothing about build
  health — a fully mocked test suite can build cleanly and pass every assertion while verifying
  nothing about real behavior (this is precisely the Chicago-vs-London distinction in
  `~/.claude/rules/testing-chicago-style.md`).
- A single evidence report can in principle need **both** facts simultaneously (a build that is
  currently broken, checked previously only via mocks). Forcing one term to stand in for the
  other would destroy that distinguishing information — this is exactly the loss the source
  fragment (`10-CE-STANDING-1.md`) warned against, and the reconciliation keeps both as
  independent, first-class terms rather than merging them.

## Canonical `ce-standing/1` vocabulary (8 terms)

The honest union of both real vocabularies, deduplicated where the sources genuinely agree,
kept separate where they genuinely diverge, is **eight** terms — not seven, because forcing
`BuildBroken` and `MOCKED` into one slot would misclassify real evidence:

1. `UNVERIFIED` — default state; no evidence checked yet. (castle: `Unknown`)
2. `ALIVE` — ran and passed, this session/this build, with real collaborators. (castle: `Alive`)
3. `PARTIAL` — some paths verified working, others not; name which paths. (castle: `PartialAlive`)
4. `BLOCKED` — a specific, citable blocker stops verification (file:line, dependency, env).
   (castle: `Blocked`)
5. `BUILD_BROKEN` — the artifact does not compile or crashes before producing a result.
   (castle: `BuildBroken`; no prior session term — new to the reconciled vocabulary)
6. `MOCKED` — a real collaborator was replaced with a fake/mock/stub for the check reported;
   the result verifies the test's model of the collaborator, not the real one. (session-only;
   no prior castle term — new to the reconciled vocabulary)
7. `UNSUPPORTED` — by design, not attempted; not a defect. (castle: `Unsupported`)
8. `REFUSED` — by design, deliberately declined; must be a real, reachable state in practice,
   not merely a theoretical enum member. (castle: `Refused`)

## Conformance carried forward from `10-CE-STANDING-1.md`

1. Closed enum, not free-text — enforced in the TypeScript artifact by a union type with no
   escape hatch (no `string` fallback member).
2. No state inherits from a neighboring claim.
3. `REFUSED` must be reachable in real use, not merely declared.

## Non-claims

- This reconciliation does not modify `~/castle/src/v26_8_18/topology.rs`. Castle's
  `ReleaseStanding` enum is left exactly as shipped; it is one of the two source vocabularies
  being reconciled, not the artifact being rewritten.
- This reconciliation does not modify `~/.claude/rules/no-overclaiming-rust.md`.
- The new shared artifact is `platform-console/app/lib/ce-standing.ts`, a TypeScript union type
  independent of both source languages, intended as the canonical term list going forward for
  code in this repo that needs to report evidence state.
- No external party has reviewed or ratified this reconciliation.

## See also

- `docs/jira/v26.8.19/10-CE-STANDING-1.md` — the fragment this file resolves
- `~/castle/src/v26_8_18/topology.rs` — castle's `ReleaseStanding` enum (unchanged)
- `~/.claude/rules/no-overclaiming-rust.md` — session vocabulary (unchanged)
- `~/.claude/rules/testing-chicago-style.md` — the Chicago/London distinction underlying `MOCKED`
- `platform-console/app/lib/ce-standing.ts` — the canonical TypeScript artifact
