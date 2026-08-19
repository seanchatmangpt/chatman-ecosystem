// ---------------------------------------------------------- AuthorityObject
//
// ce-authority/1: today, admission to execute a Castle verb
// (lib/castle.ts's resolveCastleVerb) is granted purely by static
// membership in `ALLOWED_CASTLE_VERBS` -- capability-intrinsic, not
// authority-supplied. A verb existing in that table says the verb is a
// real, safe, side-effect-free castle CLI invocation; it says nothing
// about whether THIS actor is authorized to run it RIGHT NOW (a freeze
// window may be active, or the action may itself be one of the platform's
// closed set of maker-checker-gated actions).
//
// This module is the uniform seam for that second, distinct question:
// "does authority admit this consequence?" -- composing the two ALREADY-
// REAL gates this codebase has (lib/freeze-windows.ts's checkFreezeGuard,
// lib/approval-workflow.ts's requireApproval) into ONE object other call
// sites can consult, instead of each call site re-deriving its own ad hoc
// mix of the two. `DefaultAuthorityObject` is the only implementation
// today; it is deliberately a real composition of the two real gates, not
// a new third gate -- it invents no new policy.
//
// Scope, stated honestly rather than implied: only lib/castle.ts's
// runCastleVerb consults this object as of this change (see that file's
// own comment at the call site). The platform's other DO call sites --
// the 7 actions already in lib/approval-workflow.ts's
// ACTIONS_REQUIRING_APPROVAL that route straight through requireApproval
// (org.delete, quota.override, tier.downgrade,
// backup.retention.change, export-subscription.update, dr.failover,
// dsar.erasure, plus castle.verb.schedule/freeze.override/
// environment.promote/deployment.quarantine/sla.credit.apply) -- are
// deliberately UNCHANGED and do NOT go through AuthorityObject yet. They
// keep calling requireApproval directly, exactly as before. Universal
// coverage across every mutating call site in this codebase is NOT
// claimed or built here.
import { checkFreezeGuard } from "@/lib/freeze-windows";
import {
  ACTIONS_REQUIRING_APPROVAL,
  requireApproval,
  type ApprovalAction,
} from "@/lib/approval-workflow";

/** One thing an actor is attempting to bring about. `kind` names the
 * class of consequence (e.g. `"castle.verb.run"`, or, for a consequence
 * that IS itself one of the platform's closed maker-checker actions, the
 * literal `ApprovalAction` string). `targetId` is whatever the
 * underlying gates need to scope the check -- for a freeze-guarded
 * consequence that is an org id (lib/freeze-windows.ts's windows are
 * declared per-org); for an approval-gated consequence it is the same
 * `targetId` lib/approval-workflow.ts's `ApprovalRequest` already
 * records against. */
export interface AuthorityConsequence {
  kind: string;
  targetId: string;
  actor: string;
}

export interface AuthorityDecision {
  admitted: boolean;
  /** Present only when `admitted` is `false` -- a human-readable reason
   * a caller can surface directly (an API route's error body, an audit
   * log entry). Never fabricated: it is always derived from a real
   * `checkFreezeGuard`/`requireApproval` result. */
  reason?: string;
}

/** The one shape every authority check in this codebase can be asked to
 * satisfy, regardless of which real gate(s) back it. A verb, action, or
 * mutation being CAPABLE of executing (it exists, it is well-formed) is
 * a separate, prior question from whether it is AUTHORIZED to execute
 * right now -- this interface answers only the second question. */
export interface AuthorityObject {
  admits(consequence: AuthorityConsequence): Promise<AuthorityDecision>;
}

function isApprovalAction(kind: string): kind is ApprovalAction {
  return (ACTIONS_REQUIRING_APPROVAL as string[]).includes(kind);
}

/**
 * Real composition of the two already-real gates this codebase has:
 *
 *  1. Freeze-window guard (lib/freeze-windows.ts's checkFreezeGuard):
 *     always consulted, treating `targetId` as an org id. When
 *     `targetId` does not name an org with any declared freeze windows
 *     (the common case for a non-org-scoped consequence, e.g. an
 *     org-less Castle run), this resolves to "not blocked" -- a real
 *     no-op, not a bypass, matching the same "no freeze check possible
 *     without org context" convention lib/castle.ts's runCastleVerb
 *     already documented before this object existed.
 *
 *  2. Maker-checker approval (lib/approval-workflow.ts's
 *     requireApproval): consulted only when `kind` is itself one of the
 *     platform's closed `ApprovalAction` set
 *     (ACTIONS_REQUIRING_APPROVAL). For any `kind` outside that set --
 *     including `"castle.verb.run"`, the kind lib/castle.ts's
 *     runCastleVerb passes today -- this step is a real no-op: most
 *     consequences genuinely are not in that closed set, and this
 *     object does not invent new approval requirements for them.
 *
 * Both gates must admit for `admits()` to return `{admitted: true}`.
 */
export class DefaultAuthorityObject implements AuthorityObject {
  async admits(consequence: AuthorityConsequence): Promise<AuthorityDecision> {
    const { kind, targetId, actor } = consequence;

    const freeze = await checkFreezeGuard(targetId, actor);
    if (!freeze.ok) {
      return { admitted: false, reason: freeze.error };
    }
    if (freeze.data.blocked) {
      const overrideNote = freeze.data.overrideRequest
        ? ` -- pending freeze.override approval request ${freeze.data.overrideRequest.requestId}`
        : " (no emergency override allowed for this window)";
      return {
        admitted: false,
        reason: `blocked by declared change-freeze window ${freeze.data.freeze.id}: ${freeze.data.freeze.reason}${overrideNote}`,
      };
    }

    if (isApprovalAction(kind)) {
      const approval = await requireApproval({ action: kind, targetId, requestedBy: actor });
      if (!approval.ok) {
        if ("error" in approval) {
          return { admitted: false, reason: approval.error };
        }
        return {
          admitted: false,
          reason: `requires a second, distinct owner-role approver -- pending approval request ${approval.request.requestId}`,
        };
      }
    }

    return { admitted: true };
  }
}

/** Shared singleton -- stateless (each call re-reads the two underlying
 * ConfigMap-backed gates fresh), so one instance is safe to reuse across
 * every call site that consults it. */
export const defaultAuthorityObject: AuthorityObject = new DefaultAuthorityObject();
