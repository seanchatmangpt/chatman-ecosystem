/**
 * Workforce Security-Training & Background-Check Attestation -- the
 * per-org personnel-control evidence a Fortune-5 procurement/legal
 * reviewer asks for at signing alongside this repo's other pre-signature
 * artifacts (lib/insurance-attestation.ts's COI, lib/subprocessors.ts's
 * DPA Schedule, lib/security-questionnaire-export.ts's CAIQ/SIG bundle):
 * proof that every person with real access to an org's own namespace
 * completed annual security-awareness training, and that every
 * PRIVILEGED user (role `owner` in lib/authz.ts's own Role union) has a
 * recorded background-check status -- not a spreadsheet HR keeps by
 * hand.
 *
 * Real IAM/session join, never fabricated data: the roster itself is the
 * exact `getOrgRoleAssignmentsIn` read (lib/authz.ts) every other
 * role-aware module in this repo already uses (lib/access-reviews.ts,
 * lib/sso-role-drift.ts), and each roster entry's `lastActiveAt` is a
 * real `queryAuditLog` lookup (lib/audit-db.ts) for that identifier's
 * own most recent audit row scoped to this org -- the same durable,
 * hash-chained request log every other activity signal in this console
 * is read from, not a heuristic invented for this module. Training
 * completion and background-check status are NOT derivable from IAM
 * data alone (no external HRIS/LMS integration exists in this repo), so
 * they are the reviewer's own attested input -- exactly the same
 * "reviewer decides, platform durably records the decision plus the
 * real point-in-time snapshot it was decided against" shape
 * lib/access-reviews.ts's completeAccessReview already establishes for
 * role recertification.
 *
 * Storage: one real k8s ConfigMap
 * (`platform-console-personnel-attestations`, `platform-console`
 * namespace), the exact get-then-create-or-patch
 * getConfigMap/createOrUpdateConfigMap primitive every other
 * ConfigMap-backed module in this repo already uses -- no new k8s RBAC
 * verb. One `data` key per org id (org ids are already
 * ConfigMap-key-safe `[a-z0-9-]+` slugs, same as
 * lib/access-reviews.ts), each value a JSON-encoded, APPEND-ONLY array
 * of PersonnelAttestationRecord -- no record is ever mutated or removed
 * once written, because the attestation history itself is the evidence
 * procurement/legal wants to see across renewal cycles.
 *
 * Maker-checker: recording a new attestation goes through the exact same
 * lib/approval-workflow.ts `requireApproval` gate
 * `insurance.policy.update`/`subprocessor.registry.update` already use
 * (`personnel.attestation.record`) -- this is a real security-posture
 * claim made to a THIRD PARTY at contract signing, exactly the class of
 * risk that bar already exists for. One owner's own say-so is never
 * sufficient; a second, distinct owner-role approver must sign off
 * before an attestation is durably recorded.
 */
import {
  createOrUpdateConfigMap,
  getConfigMap,
  type K8sResult,
} from "@/lib/k8s";
import { getOrgRoleAssignmentsIn, type OrgRoleAssignment, type Role } from "@/lib/authz";
import { queryAuditLog } from "@/lib/audit-db";

export const PERSONNEL_ATTESTATIONS_NAMESPACE = "platform-console";
export const PERSONNEL_ATTESTATIONS_CONFIGMAP = "platform-console-personnel-attestations";

/**
 * Annual-recertification threshold most SOC2 Type II reports cite
 * verbatim for security-awareness training ("completed at least
 * annually") -- used only to flag an org as overdue in
 * listPersonnelAttestationSummaries, never to block any action, same
 * "flag, never block" posture ACCESS_REVIEW_OVERDUE_DAYS already sets.
 */
export const PERSONNEL_ATTESTATION_OVERDUE_DAYS = 365;

export type BackgroundCheckStatus = "cleared" | "pending" | "not_required";

/** A privileged (role `owner`) identifier with no recorded background-check status is treated as this on read, never fabricated as "cleared". */
export const DEFAULT_PRIVILEGED_BACKGROUND_CHECK_STATUS: BackgroundCheckStatus = "pending";

export interface PersonnelRosterEntry {
  identifier: string;
  role: Role;
  /** True for every `owner`-role identifier -- this org's own privileged-access population, the SOC2 CC6.1 population a background-check control applies to. */
  privileged: boolean;
  /**
   * Real join against this org's own audit trail: the `ts` of this
   * identifier's most recent audit_log row scoped to this org
   * (lib/audit-db.ts's queryAuditLog), or `null` when the audit-log
   * database is unreachable/unconfigured OR this identifier has no
   * audit row yet for this org -- never a fabricated "just now".
   */
  lastActiveAt: string | null;
  securityTrainingCompleted: boolean;
  securityTrainingCompletedAt?: string;
  /** Only ever meaningful for `privileged` entries; `undefined` for a non-privileged identifier. */
  backgroundCheckStatus?: BackgroundCheckStatus;
}

export interface PersonnelAttestationRecord {
  attestedAt: string; // RFC3339, when the attester completed this attestation
  attesterIdentifier: string; // roleIdentifierFor(session) of the accountable platform owner
  /** The full role roster, joined with real audit-log activity, AS OF the moment of attestation -- a point-in-time snapshot, not a live recomputation, so a later role change never rewrites what an earlier attestation actually attested to. */
  roster: PersonnelRosterEntry[];
  trainingCompletionPercent: number; // 0-100, rounded to 1 decimal
  privilegedBackgroundCheckClearedPercent: number; // 0-100, rounded to 1 decimal, over the privileged population only
  attestationStatement: string;
}

function parseRecords(raw: string | undefined): PersonnelAttestationRecord[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (r): r is PersonnelAttestationRecord =>
        typeof r === "object" &&
        r !== null &&
        typeof (r as PersonnelAttestationRecord).attestedAt === "string" &&
        typeof (r as PersonnelAttestationRecord).attesterIdentifier === "string" &&
        Array.isArray((r as PersonnelAttestationRecord).roster) &&
        typeof (r as PersonnelAttestationRecord).trainingCompletionPercent === "number" &&
        typeof (r as PersonnelAttestationRecord).privilegedBackgroundCheckClearedPercent === "number" &&
        typeof (r as PersonnelAttestationRecord).attestationStatement === "string",
    );
  } catch {
    return [];
  }
}

/** Real read of one org's full append-only attestation history, oldest first. */
export async function getPersonnelAttestationHistory(
  orgId: string,
): Promise<K8sResult<PersonnelAttestationRecord[]>> {
  const existing = await getConfigMap(PERSONNEL_ATTESTATIONS_NAMESPACE, PERSONNEL_ATTESTATIONS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: [] };
  return { ok: true, data: parseRecords(existing.data.data[orgId]) };
}

function round1(n: number): number {
  return Math.round(n * 10) / 10;
}

/**
 * Real, current roster snapshot: this org's live role assignments
 * (getOrgRoleAssignmentsIn) joined with each identifier's real
 * last-active timestamp from this org's own audit trail
 * (queryAuditLog). Training-completion/background-check fields default
 * to `false`/`undefined` here -- they only ever become non-default
 * through a reviewer's own attested `overrides` in
 * completePersonnelAttestation, never inferred from IAM data (no field
 * in this repo's IAM state records training or background-check facts).
 * `lastActiveAt` is best-effort: when the audit-log database is
 * unreachable, every entry's `lastActiveAt` is `null` rather than
 * failing the whole snapshot -- the roster itself (the real k8s
 * ConfigMap read) is the load-bearing data this capability depends on.
 */
export async function buildPersonnelRosterSnapshot(
  orgId: string,
  namespace: string,
): Promise<K8sResult<PersonnelRosterEntry[]>> {
  const assignmentsResult = await getOrgRoleAssignmentsIn(namespace);
  if (!assignmentsResult.ok) return assignmentsResult;

  const roster = await Promise.all(
    assignmentsResult.data.map(async (a: OrgRoleAssignment): Promise<PersonnelRosterEntry> => {
      const activity = await queryAuditLog({
        actor: a.identifier,
        orgId,
        limit: 1,
        offset: 0,
      });
      const lastActiveAt = activity.ok ? (activity.data.rows[0]?.ts ?? null) : null;
      return {
        identifier: a.identifier,
        role: a.role,
        privileged: a.role === "owner",
        lastActiveAt,
        securityTrainingCompleted: false,
        ...(a.role === "owner"
          ? { backgroundCheckStatus: DEFAULT_PRIVILEGED_BACKGROUND_CHECK_STATUS }
          : {}),
      };
    }),
  );

  return { ok: true, data: roster };
}

export interface PersonnelAttestationOverride {
  identifier: string;
  securityTrainingCompleted: boolean;
  securityTrainingCompletedAt?: string;
  backgroundCheckStatus?: BackgroundCheckStatus;
}

export interface CompletePersonnelAttestationInput {
  orgId: string;
  namespace: string;
  attesterIdentifier: string;
  attestationStatement: string;
  overrides: PersonnelAttestationOverride[];
}

export interface CompletePersonnelAttestationResult {
  record: PersonnelAttestationRecord;
  history: PersonnelAttestationRecord[];
}

/**
 * The real attestation workflow -- called only with an ALREADY-APPROVED
 * payload (see the route: `requireApproval` gates the call site, same
 * "bind exactly what was approved" discipline PUT /api/owner/insurance-
 * attestation's own route establishes). Builds the current roster
 * snapshot, applies only the overrides for identifiers actually present
 * in that snapshot (a caller-supplied identifier that isn't in the
 * current roster is dropped, never fabricated as attested -- same
 * discipline lib/access-reviews.ts's completeAccessReview applies to
 * `revokedIdentifiers`), computes the two real completion percentages,
 * and appends one new record to the org's append-only history.
 */
export async function completePersonnelAttestation(
  input: CompletePersonnelAttestationInput,
): Promise<K8sResult<CompletePersonnelAttestationResult>> {
  const snapshotResult = await buildPersonnelRosterSnapshot(input.orgId, input.namespace);
  if (!snapshotResult.ok) return snapshotResult;

  const overrideByIdentifier = new Map(input.overrides.map((o) => [o.identifier, o]));

  const roster = snapshotResult.data.map((entry): PersonnelRosterEntry => {
    const override = overrideByIdentifier.get(entry.identifier);
    if (!override) return entry;
    return {
      ...entry,
      securityTrainingCompleted: override.securityTrainingCompleted,
      ...(override.securityTrainingCompletedAt
        ? { securityTrainingCompletedAt: override.securityTrainingCompletedAt }
        : {}),
      ...(entry.privileged && override.backgroundCheckStatus
        ? { backgroundCheckStatus: override.backgroundCheckStatus }
        : {}),
    };
  });

  const trainingCompletionPercent =
    roster.length === 0
      ? 100
      : round1((roster.filter((r) => r.securityTrainingCompleted).length / roster.length) * 100);

  const privileged = roster.filter((r) => r.privileged);
  const privilegedBackgroundCheckClearedPercent =
    privileged.length === 0
      ? 100
      : round1((privileged.filter((r) => r.backgroundCheckStatus === "cleared").length / privileged.length) * 100);

  const record: PersonnelAttestationRecord = {
    attestedAt: new Date().toISOString(),
    attesterIdentifier: input.attesterIdentifier,
    roster,
    trainingCompletionPercent,
    privilegedBackgroundCheckClearedPercent,
    attestationStatement: input.attestationStatement,
  };

  const existingHistoryResult = await getPersonnelAttestationHistory(input.orgId);
  if (!existingHistoryResult.ok) return existingHistoryResult;
  const history = [...existingHistoryResult.data, record];

  const write = await createOrUpdateConfigMap(
    PERSONNEL_ATTESTATIONS_NAMESPACE,
    PERSONNEL_ATTESTATIONS_CONFIGMAP,
    { [input.orgId]: JSON.stringify(history) },
  );
  if (!write.ok) return write;

  return { ok: true, data: { record, history } };
}

export const PERSONNEL_ROSTER_SNAPSHOTS_CONFIGMAP = "platform-console-personnel-roster-snapshots";

export interface PersonnelRosterSnapshot {
  capturedAt: string; // RFC3339
  orgId: string;
  privilegedCount: number;
  totalCount: number;
  /** Count of `privileged` identifiers with no audit-log activity in the last 90 days (or never) -- a real signal for which owner-role identifiers a reviewer should prioritize re-attesting/removing, independent of and never a substitute for a completed attestation. */
  privilegedInactive90dCount: number;
}

/**
 * Real, unattended-poller counterpart to buildPersonnelRosterSnapshot --
 * computes the SAME real IAM/audit-log join and persists a compact,
 * durable trend point (never the full per-identifier roster, which
 * belongs only in an attested PersonnelAttestationRecord) to this org's
 * append-only history. Purely a READ-then-PERSIST of already-real data,
 * same "no approval needed, nothing is claimed or attested" boundary
 * lib/sso-role-drift-history.ts's own snapshot append already
 * establishes -- this never substitutes for, and is never confused
 * with, a human-attested PersonnelAttestationRecord above.
 */
export async function appendPersonnelRosterSnapshot(
  orgId: string,
  namespace: string,
): Promise<K8sResult<PersonnelRosterSnapshot>> {
  const rosterResult = await buildPersonnelRosterSnapshot(orgId, namespace);
  if (!rosterResult.ok) return rosterResult;
  const roster = rosterResult.data;

  const now = Date.now();
  const privileged = roster.filter((r) => r.privileged);
  const privilegedInactive90dCount = privileged.filter((r) => {
    if (!r.lastActiveAt) return true;
    const days = (now - Date.parse(r.lastActiveAt)) / (24 * 60 * 60 * 1000);
    return days > 90;
  }).length;

  const snapshot: PersonnelRosterSnapshot = {
    capturedAt: new Date().toISOString(),
    orgId,
    privilegedCount: privileged.length,
    totalCount: roster.length,
    privilegedInactive90dCount,
  };

  const existing = await getConfigMap(PERSONNEL_ATTESTATIONS_NAMESPACE, PERSONNEL_ROSTER_SNAPSHOTS_CONFIGMAP);
  if (!existing.ok) return existing;
  const history: PersonnelRosterSnapshot[] = (() => {
    const raw = existing.data?.data[orgId];
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw) as unknown;
      return Array.isArray(parsed) ? (parsed as PersonnelRosterSnapshot[]) : [];
    } catch {
      return [];
    }
  })();
  history.push(snapshot);

  const write = await createOrUpdateConfigMap(
    PERSONNEL_ATTESTATIONS_NAMESPACE,
    PERSONNEL_ROSTER_SNAPSHOTS_CONFIGMAP,
    { [orgId]: JSON.stringify(history) },
  );
  if (!write.ok) return write;

  return { ok: true, data: snapshot };
}

export interface PersonnelAttestationSummary {
  orgId: string;
  lastAttestedAt: string | null;
  daysSinceLastAttestation: number | null; // null when never attested
  attestationCount: number;
  lastTrainingCompletionPercent: number | null;
  lastPrivilegedBackgroundCheckClearedPercent: number | null;
  overdue: boolean; // true when never attested, or daysSinceLastAttestation > PERSONNEL_ATTESTATION_OVERDUE_DAYS
}

/**
 * Real per-org summary across every org that has EVER had an attestation
 * recorded, sorted descending by daysSinceLastAttestation (nulls --
 * never attested -- sort first), same shape and same "never-attested org
 * still appears, that gap is the whole point" discipline
 * lib/access-reviews.ts's listAccessReviewSummaries already establishes.
 */
export async function listPersonnelAttestationSummaries(
  knownOrgIds: string[],
): Promise<K8sResult<PersonnelAttestationSummary[]>> {
  const existing = await getConfigMap(PERSONNEL_ATTESTATIONS_NAMESPACE, PERSONNEL_ATTESTATIONS_CONFIGMAP);
  if (!existing.ok) return existing;
  const data = existing.data?.data ?? {};

  const now = Date.now();
  const summaries: PersonnelAttestationSummary[] = knownOrgIds.map((orgId) => {
    const history = parseRecords(data[orgId]);
    const last = history.length > 0 ? history[history.length - 1] : null;
    const daysSinceLastAttestation = last
      ? Math.floor((now - Date.parse(last.attestedAt)) / (24 * 60 * 60 * 1000))
      : null;
    return {
      orgId,
      lastAttestedAt: last?.attestedAt ?? null,
      daysSinceLastAttestation,
      attestationCount: history.length,
      lastTrainingCompletionPercent: last?.trainingCompletionPercent ?? null,
      lastPrivilegedBackgroundCheckClearedPercent: last?.privilegedBackgroundCheckClearedPercent ?? null,
      overdue: daysSinceLastAttestation === null || daysSinceLastAttestation > PERSONNEL_ATTESTATION_OVERDUE_DAYS,
    };
  });

  summaries.sort((a, b) => {
    if (a.daysSinceLastAttestation === null && b.daysSinceLastAttestation === null) return 0;
    if (a.daysSinceLastAttestation === null) return -1;
    if (b.daysSinceLastAttestation === null) return 1;
    return b.daysSinceLastAttestation - a.daysSinceLastAttestation;
  });

  return { ok: true, data: summaries };
}
