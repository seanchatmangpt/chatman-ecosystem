/**
 * Per-org named-user access review attestation -- the SOC2 CC6.1/CC6.3
 * and ISO27001 A.9.2.5 audit artifact this console's existing custom RBAC
 * (lib/authz.ts's platform-console-org-roles ConfigMap, per-org
 * namespace-scoped) has never recorded: evidence that an accountable
 * owner actually reviewed a point-in-time snapshot of an org's role
 * assignments and either confirmed them or revoked what shouldn't still
 * be there. Role assignment and role removal already existed
 * (setOrgRoleIn/removeOrgRoleIn); this module adds the missing durable
 * *review event* record a Fortune-5 vendor-security team's auditor
 * actually asks for during a Type II audit -- "show me the last four
 * quarterly reviews and who signed each one," not just "show me the
 * current role list."
 *
 * Storage: one real k8s ConfigMap, `platform-access-reviews` in the
 * `platform-console` namespace -- reusing the exact
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch primitive
 * every other ConfigMap-backed module in this repo (lib/authz.ts,
 * lib/custom-roles.ts, lib/orgs.ts) already uses, so this needs zero new
 * k8s RBAC verbs (the existing platform-console-feature-flags Role
 * already grants get/list/create/update/patch on configmaps with no
 * resourceNames restriction -- see lib/authz.ts's own header comment for
 * the same argument applied to platform-console-org-roles).
 *
 * One `data` key per org id (k8s ConfigMap keys must match
 * `[-._a-zA-Z0-9]+`; org ids minted by lib/orgs.ts's createOrg are
 * already `[a-z0-9-]+` slugs, so no escaping is needed here, unlike
 * lib/authz.ts's identifier keys which must carry arbitrary emails).
 * Each key's value is a JSON-encoded array of AccessReviewRecord,
 * APPEND-ONLY -- completeAccessReview always reads the existing array and
 * writes it back with one new record pushed on the end; no record is
 * ever mutated or removed once written, because the review history
 * itself is the audit trail.
 */
import {
  createOrUpdateConfigMap,
  getConfigMap,
  type K8sResult,
} from "@/lib/k8s";
import { getOrgRoleAssignmentsIn, removeOrgRoleIn, type OrgRoleAssignment } from "@/lib/authz";

export const ACCESS_REVIEWS_NAMESPACE = "platform-console";
export const ACCESS_REVIEWS_CONFIGMAP = "platform-access-reviews";

/**
 * A quarterly-recertification threshold most SOC2 Type II reports and
 * ISO27001 A.9.2.5 controls cite verbatim ("access rights reviewed at
 * regular intervals, e.g. quarterly") -- used only to flag an org as
 * overdue in listAccessReviewSummaries, never to block any action.
 */
export const ACCESS_REVIEW_OVERDUE_DAYS = 90;

export interface AccessReviewRecord {
  reviewedAt: string; // RFC3339, when the reviewer completed this review
  reviewerIdentifier: string; // roleIdentifierFor(session) of the accountable owner/admin
  /**
   * The full org-roles ConfigMap content (identifier -> role, decoded
   * keys) AS OF the moment of review, captured via the existing
   * getOrgRoleAssignmentsIn (which itself wraps lib/k8s.ts's
   * getConfigMap) -- a real point-in-time snapshot, not a live
   * recomputation, so a later role change never rewrites what an earlier
   * review actually attested to.
   */
  roleSnapshot: OrgRoleAssignment[];
  // Identifiers the reviewer removed as part of this review (a subset of
  // roleSnapshot's identifiers). Empty when the review confirmed every
  // assignment as still necessary.
  revokedIdentifiers: string[];
  attestationStatement: string;
}

function parseReviews(raw: string | undefined): AccessReviewRecord[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (r): r is AccessReviewRecord =>
        typeof r === "object" &&
        r !== null &&
        typeof (r as AccessReviewRecord).reviewedAt === "string" &&
        typeof (r as AccessReviewRecord).reviewerIdentifier === "string" &&
        Array.isArray((r as AccessReviewRecord).roleSnapshot) &&
        Array.isArray((r as AccessReviewRecord).revokedIdentifiers) &&
        typeof (r as AccessReviewRecord).attestationStatement === "string",
    );
  } catch {
    return [];
  }
}

/** Real read of one org's full append-only review history, oldest first. */
export async function getAccessReviewHistory(
  orgId: string,
): Promise<K8sResult<AccessReviewRecord[]>> {
  const existing = await getConfigMap(ACCESS_REVIEWS_NAMESPACE, ACCESS_REVIEWS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: [] };
  return { ok: true, data: parseReviews(existing.data.data[orgId]) };
}

export interface CompleteAccessReviewInput {
  orgId: string;
  namespace: string; // the org's own namespace (getOrg(orgId).data.namespace)
  reviewerIdentifier: string;
  revokedIdentifiers: string[];
  attestationStatement: string;
}

export interface CompleteAccessReviewResult {
  record: AccessReviewRecord;
  history: AccessReviewRecord[];
  revokedCount: number;
}

/**
 * The real review workflow: snapshot the org's CURRENT role assignments
 * (from its own namespace-local platform-console-org-roles ConfigMap --
 * the same one setOrgRoleIn/getOrgRoleAssignmentsIn already operate on),
 * apply every revocation the reviewer specified via the existing
 * removeOrgRoleIn, then append one new AccessReviewRecord to the org's
 * append-only review history. The snapshot captured is the PRE-revocation
 * state -- "here is exactly what I reviewed, and here is what I decided
 * to remove from it" -- which is what an auditor actually wants to see,
 * not a post-revocation list that hides what was revoked.
 */
export async function completeAccessReview(
  input: CompleteAccessReviewInput,
): Promise<K8sResult<CompleteAccessReviewResult>> {
  const snapshotResult = await getOrgRoleAssignmentsIn(input.namespace);
  if (!snapshotResult.ok) return snapshotResult;
  const roleSnapshot = snapshotResult.data;
  const snapshotIdentifiers = new Set(roleSnapshot.map((a) => a.identifier));

  // Only ever revoke identifiers that were actually present in the
  // snapshot being reviewed -- a caller-supplied identifier that isn't
  // in the current role list is dropped, never fabricated as "revoked".
  const revokedIdentifiers = Array.from(
    new Set(input.revokedIdentifiers.filter((id) => snapshotIdentifiers.has(id))),
  );

  for (const identifier of revokedIdentifiers) {
    const removed = await removeOrgRoleIn(input.namespace, identifier);
    if (!removed.ok) return removed;
  }

  const record: AccessReviewRecord = {
    reviewedAt: new Date().toISOString(),
    reviewerIdentifier: input.reviewerIdentifier,
    roleSnapshot,
    revokedIdentifiers,
    attestationStatement: input.attestationStatement,
  };

  const existingHistoryResult = await getAccessReviewHistory(input.orgId);
  if (!existingHistoryResult.ok) return existingHistoryResult;
  const history = [...existingHistoryResult.data, record];

  const write = await createOrUpdateConfigMap(ACCESS_REVIEWS_NAMESPACE, ACCESS_REVIEWS_CONFIGMAP, {
    [input.orgId]: JSON.stringify(history),
  });
  if (!write.ok) return write;

  return { ok: true, data: { record, history, revokedCount: revokedIdentifiers.length } };
}

export interface AccessReviewSummary {
  orgId: string;
  lastReviewedAt: string | null;
  lastReviewerIdentifier: string | null;
  daysSinceLastReview: number | null; // null when never reviewed
  reviewCount: number;
  overdue: boolean; // true when never reviewed, or daysSinceLastReview > ACCESS_REVIEW_OVERDUE_DAYS
}

/**
 * Real per-org summary across every org that has EVER had a review
 * recorded, sorted descending by daysSinceLastReview (nulls -- never
 * reviewed -- sort first, as the most overdue possible state) so a
 * compliance dashboard can render the most-overdue orgs at the top
 * without any client-side re-sort.
 *
 * `knownOrgIds` (every org id from lib/orgs.ts's listOrgs) is required so
 * an org that has NEVER been reviewed still appears with
 * daysSinceLastReview: null / overdue: true -- the whole point of this
 * summary is to surface exactly that gap, which a ConfigMap-keys-only
 * scan could never do (a never-reviewed org has no key at all).
 */
export async function listAccessReviewSummaries(
  knownOrgIds: string[],
): Promise<K8sResult<AccessReviewSummary[]>> {
  const existing = await getConfigMap(ACCESS_REVIEWS_NAMESPACE, ACCESS_REVIEWS_CONFIGMAP);
  if (!existing.ok) return existing;
  const data = existing.data?.data ?? {};

  const now = Date.now();
  const summaries: AccessReviewSummary[] = knownOrgIds.map((orgId) => {
    const history = parseReviews(data[orgId]);
    const last = history.length > 0 ? history[history.length - 1] : null;
    const daysSinceLastReview = last
      ? Math.floor((now - Date.parse(last.reviewedAt)) / (24 * 60 * 60 * 1000))
      : null;
    return {
      orgId,
      lastReviewedAt: last?.reviewedAt ?? null,
      lastReviewerIdentifier: last?.reviewerIdentifier ?? null,
      daysSinceLastReview,
      reviewCount: history.length,
      overdue: daysSinceLastReview === null || daysSinceLastReview > ACCESS_REVIEW_OVERDUE_DAYS,
    };
  });

  summaries.sort((a, b) => {
    if (a.daysSinceLastReview === null && b.daysSinceLastReview === null) return 0;
    if (a.daysSinceLastReview === null) return -1;
    if (b.daysSinceLastReview === null) return 1;
    return b.daysSinceLastReview - a.daysSinceLastReview;
  });

  return { ok: true, data: summaries };
}
