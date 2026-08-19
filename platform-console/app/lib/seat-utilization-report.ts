/**
 * Real, persisted Seat/License Utilization Report SNAPSHOT history --
 * quarterly true-up evidence for a Fortune-5 buyer's Procurement/IT-Asset-
 * Management team, distinct from the two capabilities this codebase
 * already ships that look adjacent but answer a different question:
 *
 *   - app/api/access-reviews (named-user access-review attestation) is a
 *     SECURITY signoff: "does every named user still need the access they
 *     have," reviewed and attested by a security owner.
 *   - app/api/qbr (QBR bundle) is a BUSINESS-REVIEW artifact: usage
 *     trends, incidents, and roadmap for an executive relationship
 *     conversation.
 *
 * This module answers neither -- it answers "are we paying for seats
 * nobody is using," the narrow utilization/cost artifact a procurement
 * stakeholder needs to right-size a seat-based contract at renewal:
 * purchased-vs-active seat counts, invited-but-never-accepted seats, and
 * seats that ARE assigned a role but haven't been used in 60+ days
 * (stale), each carrying a real illustrative dollar cost of the waste.
 *
 * Every number here is computed from real, already-persisted state --
 * never fabricated or interpolated:
 *   - seatsPurchased: lib/tiers.ts's real per-tier SEAT_LIMITS, keyed off
 *     lib/orgs.ts's getOrgProjectTier (the real Project CR tier label).
 *   - seatsActive / seatsInvitedUnaccepted: lib/authz.ts's real
 *     getOrgRoleAssignmentsIn / listOrgInvitesIn reads of the same
 *     `platform-console-org-roles` ConfigMap countUsedSeatsIn already
 *     reads for the live /org/seats page -- this module reuses that same
 *     read, not a second implementation of seat counting.
 *   - staleSeats: cross-referenced against lib/active-sessions.ts's real
 *     Postgres-backed `active_sessions` registry (the same store backing
 *     /sessions) -- an assigned identifier with no session row, or whose
 *     most recent `lastSeenAt` is older than STALE_THRESHOLD_DAYS, counts
 *     as stale. An identifier that has genuinely never logged in (no row
 *     at all) is treated as stale, not silently excluded -- that is the
 *     single most actionable line item a true-up review looks for.
 *
 * Storage follows lib/cost-report-history.ts's exact
 * get-then-append-then-cap-then-patch ConfigMap convention: one
 * `platform-console-seat-utilization-history` ConfigMap in the
 * `platform-console` namespace, one JSON-stringified capped array per
 * key -- keyed by `orgId` (per this capability's own spec), NOT by
 * namespace, since a procurement stakeholder identifies their contract by
 * org, not by cluster namespace.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { getOrg, getOrgProjectTier } from "@/lib/orgs";
import { getOrgRoleAssignmentsIn, listOrgInvitesIn } from "@/lib/authz";
import { listActiveSessions } from "@/lib/active-sessions";
import { SEAT_LIMITS } from "@/lib/tiers";

export const SEAT_UTILIZATION_NAMESPACE = "platform-console";
export const SEAT_UTILIZATION_CONFIGMAP = "platform-console-seat-utilization-history";

/** Most recent monthly snapshots kept per org -- 24 months (2 years) of
 * true-up history, the same "bound the ConfigMap value well under k8s's
 * 1MiB ceiling" reasoning as lib/cost-report-history.ts's
 * MAX_SNAPSHOTS_PER_NAMESPACE, sized here to this capability's own
 * monthly (not daily) cadence per this capability's spec. */
export const MAX_SNAPSHOTS_PER_ORG = 24;

/** An assigned seat with no session activity in this many days counts as
 * stale for the true-up -- the "unused seat" line item a procurement
 * reviewer right-sizes a renewal against. */
export const STALE_THRESHOLD_DAYS = 60;

/** Explicitly illustrative monthly dollar cost per seat -- same
 * "labeled illustrative, not a real contracted price" discipline as
 * lib/invoice-preview.ts's ILLUSTRATIVE_RATES; this module performs real
 * arithmetic (staleSeats * this rate) over real counted seats, never a
 * fabricated total. */
export const ILLUSTRATIVE_SEAT_COST_MONTHLY = 75;

export interface SeatUtilizationSnapshot {
  orgId: string;
  periodStart: string; // RFC3339, first instant of the covered month
  periodEnd: string; // RFC3339, instant the snapshot was generated
  seatsPurchased: number;
  seatsActive: number;
  seatsInvitedUnaccepted: number;
  staleSeats: number;
  estimatedWastedSeatCost: number;
  generatedAt: string; // RFC3339
}

type SnapshotRegistry = Record<string, SeatUtilizationSnapshot[]>;

function isSeatUtilizationSnapshot(value: unknown): value is SeatUtilizationSnapshot {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.orgId === "string" &&
    typeof v.periodStart === "string" &&
    typeof v.periodEnd === "string" &&
    typeof v.seatsPurchased === "number" &&
    typeof v.seatsActive === "number" &&
    typeof v.seatsInvitedUnaccepted === "number" &&
    typeof v.staleSeats === "number" &&
    typeof v.estimatedWastedSeatCost === "number" &&
    typeof v.generatedAt === "string"
  );
}

async function getRegistry(): Promise<K8sResult<SnapshotRegistry>> {
  const existing = await getConfigMap(SEAT_UTILIZATION_NAMESPACE, SEAT_UTILIZATION_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: SnapshotRegistry = {};
  for (const [orgId, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (Array.isArray(rows)) {
        parsed[orgId] = rows.filter(isSeatUtilizationSnapshot);
      }
    } catch {
      // A hand-edited or corrupt registry entry is skipped, not fatal --
      // same "one bad row doesn't break the whole list" discipline
      // lib/cost-report-history.ts's own getRegistry already uses.
    }
  }
  return { ok: true, data: parsed };
}

/**
 * Real, chronological (oldest first) snapshot history for one org. `[]`
 * -- not an error -- for an org with no snapshots yet, same "empty list
 * is not a failure" convention as lib/cost-report-history.ts's
 * listCostReportSnapshots.
 */
export async function listSeatUtilizationSnapshots(
  orgId: string,
): Promise<K8sResult<SeatUtilizationSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;
  return { ok: true, data: registry.data[orgId] ?? [] };
}

/**
 * Appends one real snapshot for `orgId`, capped to the most recent
 * `MAX_SNAPSHOTS_PER_ORG`. Performs no computation of its own -- callers
 * pass an already-computed `SeatUtilizationSnapshot` (normally the result
 * of `generateSeatUtilizationSnapshot` below), same
 * compute-then-append-then-cap-then-patch split as
 * lib/cost-report-history.ts's appendCostReportSnapshot.
 */
export async function appendSeatUtilizationSnapshot(
  snapshot: SeatUtilizationSnapshot,
): Promise<K8sResult<SeatUtilizationSnapshot[]>> {
  const registry = await getRegistry();
  if (!registry.ok) return registry;

  const existing = registry.data[snapshot.orgId] ?? [];
  const updated = [...existing, snapshot].slice(-MAX_SNAPSHOTS_PER_ORG);

  const result = await createOrUpdateConfigMap(
    SEAT_UTILIZATION_NAMESPACE,
    SEAT_UTILIZATION_CONFIGMAP,
    { [snapshot.orgId]: JSON.stringify(updated) },
  );
  if (!result.ok) return result;

  return { ok: true, data: updated };
}

/**
 * Real computation of one org's current seat utilization -- the read
 * side this module exists for. `orgId` resolution follows the exact same
 * convention every `/api/orgs/[id]/*` route in this tree uses (see
 * lib/cost-report-history.ts-backed routes' own header comments): resolve
 * `orgId` against the real `platform-console-orgs` registry first; when
 * it doesn't resolve there, `orgId` is used directly as both the org id
 * AND the k8s namespace -- this deployment's one real single-tenant case.
 *
 * `periodStart` is the first instant (UTC) of the calendar month
 * `generatedAt` falls in; `periodEnd` is `generatedAt` itself -- a
 * monthly snapshot always covers "this month so far," the same
 * "real, honest window per firing" discipline
 * app/api/internal/cost-report-snapshot's own SNAPSHOT_WINDOW_HOURS
 * comment already establishes for its own (daily) cadence.
 */
export async function generateSeatUtilizationSnapshot(
  orgId: string,
): Promise<K8sResult<SeatUtilizationSnapshot>> {
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) return orgResult;
  const namespace = orgResult.data ? orgResult.data.namespace : orgId;

  const [tierResult, rolesResult, invitesResult, sessionsResult] = await Promise.all([
    getOrgProjectTier(namespace),
    getOrgRoleAssignmentsIn(namespace),
    listOrgInvitesIn(namespace),
    listActiveSessions(),
  ]);

  if (!tierResult.ok) return tierResult;
  if (!rolesResult.ok) return rolesResult;
  if (!invitesResult.ok) return invitesResult;

  // The active-session registry is real but, per its own header comment,
  // fails OPEN (allows the request through) when its Postgres is
  // genuinely unreachable -- here that same unreachability degrades to
  // "no session data available," which this report treats as EVERY
  // assigned seat being unable to prove recent activity (stale), the
  // fail-closed direction for a cost-waste report: an unreachable
  // registry must never silently under-count staleness.
  const lastSeenByIdentifier = new Map<string, number>();
  if (sessionsResult.ok) {
    for (const record of sessionsResult.data) {
      const seenAt = new Date(record.lastSeenAt).getTime();
      const prior = lastSeenByIdentifier.get(record.identifier);
      if (prior === undefined || seenAt > prior) {
        lastSeenByIdentifier.set(record.identifier, seenAt);
      }
    }
  }

  const generatedAt = new Date();
  const staleThresholdMs = STALE_THRESHOLD_DAYS * 24 * 60 * 60 * 1000;
  const staleCutoff = generatedAt.getTime() - staleThresholdMs;

  const seatsActive = rolesResult.data.length;
  let staleSeats = 0;
  for (const assignment of rolesResult.data) {
    const lastSeen = lastSeenByIdentifier.get(assignment.identifier);
    if (lastSeen === undefined || lastSeen < staleCutoff) {
      staleSeats += 1;
    }
  }

  const now = Date.now();
  const seatsInvitedUnaccepted = invitesResult.data.filter(
    (invite) => invite.status === "pending" && new Date(invite.expiresAt).getTime() > now,
  ).length;

  const seatsPurchased = SEAT_LIMITS[tierResult.data];
  const estimatedWastedSeatCost = staleSeats * ILLUSTRATIVE_SEAT_COST_MONTHLY;

  const periodStart = new Date(
    Date.UTC(generatedAt.getUTCFullYear(), generatedAt.getUTCMonth(), 1, 0, 0, 0, 0),
  );

  const snapshot: SeatUtilizationSnapshot = {
    orgId,
    periodStart: periodStart.toISOString(),
    periodEnd: generatedAt.toISOString(),
    seatsPurchased,
    seatsActive,
    seatsInvitedUnaccepted,
    staleSeats,
    estimatedWastedSeatCost,
    generatedAt: generatedAt.toISOString(),
  };

  return { ok: true, data: snapshot };
}
