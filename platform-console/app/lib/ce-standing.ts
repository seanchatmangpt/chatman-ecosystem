/**
 * ce-standing/1 — canonical, closed evidence-state vocabulary.
 *
 * Reconciles two real, independently-evolved vocabularies:
 *   - castle's Rust enum `ReleaseStanding` (~/castle/src/v26_8_18/topology.rs:38-46)
 *   - this repo's session vocabulary in `~/.claude/rules/no-overclaiming-rust.md`
 *
 * Full reconciliation and mapping table:
 *   docs/jira/v26.8.19/CE-STANDING-RECONCILED.md
 *
 * This is a CLOSED union — 8 terms, no `string` escape hatch. `BUILD_BROKEN` and `MOCKED`
 * are kept as separate, orthogonal terms on purpose: `BUILD_BROKEN` is an artifact-health
 * fact (does it compile/run), `MOCKED` is a test-methodology fact (was a real collaborator
 * faked). Collapsing them into one term would lose real distinguishing information — see
 * the reconciliation doc's "genuine divergence" section.
 */
export type CeStanding =
  | "UNVERIFIED"
  | "ALIVE"
  | "PARTIAL"
  | "BLOCKED"
  | "BUILD_BROKEN"
  | "MOCKED"
  | "UNSUPPORTED"
  | "REFUSED";

/**
 * Precise definition for each term, written so two independent parties classifying the same
 * evidence land on the same term. Each entry also names its nearest castle `ReleaseStanding`
 * variant where one exists (`castleEquivalent: null` marks a term with no castle counterpart).
 */
export interface CeStandingDefinition {
  /** One-sentence, unambiguous classification rule. */
  readonly definition: string;
  /** The castle `ReleaseStanding` variant this term corresponds to, or null if none exists. */
  readonly castleEquivalent:
    | "Unknown"
    | "PartialAlive"
    | "Alive"
    | "Blocked"
    | "BuildBroken"
    | "Unsupported"
    | "Refused"
    | null;
}

/**
 * The canonical definition table. Use this — not ad hoc prose — as the single source of
 * truth when classifying evidence or reviewing a classification.
 */
export const CE_STANDING_DEFINITIONS: Readonly<Record<CeStanding, CeStandingDefinition>> = {
  UNVERIFIED: {
    definition:
      "Default state. No evidence has been checked yet for this claim, this session/build. " +
      "Never round up from here without a command and its real output.",
    castleEquivalent: "Unknown",
  },
  ALIVE: {
    definition:
      "Ran and passed, this session/this build, exercising real collaborators (not mocks). " +
      "Cite the exact command and its exit status as evidence.",
    castleEquivalent: "Alive",
  },
  PARTIAL: {
    definition:
      "Some paths/subsystems verified working, others not yet verified or verified failing. " +
      "Must name which specific paths are ALIVE and which are not, not just assert 'partial'.",
    castleEquivalent: "PartialAlive",
  },
  BLOCKED: {
    definition:
      "A specific, citable blocker (file:line, missing dependency, unavailable environment) " +
      "prevents verification right now. The build itself may be healthy — only verification " +
      "is stopped. Cite the exact blocker.",
    castleEquivalent: "Blocked",
  },
  BUILD_BROKEN: {
    definition:
      "Artifact-health fact: the code does not compile, or crashes/panics before producing a " +
      "result. Orthogonal to test methodology — says nothing about whether prior checks used " +
      "mocks. Distinct from BLOCKED, which allows a healthy build stopped by an external factor.",
    castleEquivalent: "BuildBroken",
  },
  MOCKED: {
    definition:
      "Test-methodology fact: a real collaborator (subprocess, file, network service) was " +
      "replaced with a fake/mock/stub for the check being reported. The result verifies the " +
      "test's model of the collaborator, not the real one. Orthogonal to build health — a " +
      "fully mocked suite can build and pass while verifying nothing real. No castle " +
      "equivalent; do not conflate with BUILD_BROKEN.",
    castleEquivalent: null,
  },
  UNSUPPORTED: {
    definition:
      "By design, not attempted for this target/platform/scope. Not a defect — a deliberate " +
      "scoping decision, distinct from REFUSED (which is a runtime/policy decline rather than " +
      "an out-of-scope declaration).",
    castleEquivalent: "Unsupported",
  },
  REFUSED: {
    definition:
      "By design, deliberately declined (e.g. a guardrail or policy blocked the action). Must " +
      "be a real, reachable state in actual use — a vocabulary where nothing can ever be " +
      "REFUSED is not doing real classification work.",
    castleEquivalent: "Refused",
  },
} as const;

/** All eight canonical terms, in the order defined in the reconciliation doc. */
export const CE_STANDING_VALUES: readonly CeStanding[] = [
  "UNVERIFIED",
  "ALIVE",
  "PARTIAL",
  "BLOCKED",
  "BUILD_BROKEN",
  "MOCKED",
  "UNSUPPORTED",
  "REFUSED",
] as const;

/** Type guard: narrows an arbitrary string to `CeStanding` if it is one of the 8 canonical terms. */
export function isCeStanding(value: string): value is CeStanding {
  return (CE_STANDING_VALUES as readonly string[]).includes(value);
}
