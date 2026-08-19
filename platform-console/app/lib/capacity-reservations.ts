/**
 * Real Committed-Use Capacity Reservations (AWS Reserved Instances / GCP
 * Committed Use Discounts equivalent): a forward commitment against
 * future usage, distinct from every ceiling/overage capability already
 * built in this repo. lib/tiers.ts's TIER_RESOURCE_QUOTAS is a fixed
 * per-tier ResourceQuota ceiling set once at provisioning time;
 * lib/overage-billing.ts only ever REACTS after the fact to usage that
 * bursts past that ceiling. Neither lets an org pre-commit to and
 * pre-pay for capacity ABOVE their tier's default ceiling in exchange
 * for a discount on the overage rate that usage-based billing already
 * computes -- the multi-billion-dollar procurement line item AWS RI /
 * GCP CUD actually are (finance wants predictable annual spend,
 * engineering wants guaranteed headroom).
 *
 * Storage: one real k8s ConfigMap, `platform-console-capacity-
 * reservations`, in the `platform-console` namespace -- same "no new k8s
 * resource kind, one key per tenant, JSON value" convention every other
 * ConfigMap-backed module in this codebase already uses
 * (lib/stripe-billing.ts's subscriptions ConfigMap, lib/orgs.ts's
 * registry ConfigMap). Key shape: `reservation.<orgId>` ->
 * JSON-encoded CapacityReservation.
 *
 * Enforcement: `createReservation` raises the namespace's real
 * ResourceQuota.spec.hard to the committed level IMMEDIATELY via
 * lib/k8s.ts's existing `patchResourceQuotaHard` -- the exact same real
 * RFC 7386 merge-patch primitive `createOrUpdateResourceQuota`/
 * lib/plan-state.ts's suspend path already use, so a reservation's
 * headroom guarantee is enforced by the same kube-apiserver admission-
 * time check every other quota ceiling in this app already relies on --
 * no new k8s verb. `cancelReservation` and the expiry sweep
 * (`sweepExpiredReservations`) revert that ceiling back to the org's
 * real Project tier default (`resourceQuotaHardFor`), never leaving a
 * stale, unpaid-for ceiling in place once the commitment lapses.
 *
 * Pricing: lib/invoice-preview.ts's `computeLineItems` is the one place
 * a reservation's `discountPct` actually turns into a dollar amount --
 * this module only stores and enforces the commitment; it makes no
 * pricing decision of its own.
 */
import {
  createOrUpdateConfigMap,
  getConfigMap,
  k8sRequest,
  patchResourceQuotaHard,
  type K8sResult,
} from "@/lib/k8s";
import { getOrgProjectTier } from "@/lib/orgs";
import {
  isReservationTermMonths,
  reservationDiscountPct,
  resourceQuotaHardFor,
  type ProjectTier,
  type ReservationTermMonths,
} from "@/lib/tiers";

export const RESERVATIONS_NAMESPACE = "platform-console";
export const RESERVATIONS_CONFIGMAP = "platform-console-capacity-reservations";

function reservationConfigMapKey(orgId: string): string {
  return `reservation.${orgId}`;
}

export interface CapacityReservation {
  orgId: string;
  namespace: string;
  tier: ProjectTier;
  committedCpuCores: number;
  committedMemoryGi: number;
  termMonths: ReservationTermMonths;
  discountPct: number;
  startDate: string;
  endDate: string;
  createdBy: string;
}

function parseStoredReservation(orgId: string, raw: string): CapacityReservation | null {
  try {
    const p = JSON.parse(raw) as Partial<CapacityReservation>;
    if (
      typeof p.namespace === "string" &&
      typeof p.tier === "string" &&
      typeof p.committedCpuCores === "number" &&
      typeof p.committedMemoryGi === "number" &&
      typeof p.termMonths === "number" &&
      typeof p.discountPct === "number" &&
      typeof p.startDate === "string" &&
      typeof p.endDate === "string" &&
      typeof p.createdBy === "string"
    ) {
      return {
        orgId,
        namespace: p.namespace,
        tier: p.tier as ProjectTier,
        committedCpuCores: p.committedCpuCores,
        committedMemoryGi: p.committedMemoryGi,
        termMonths: p.termMonths as ReservationTermMonths,
        discountPct: p.discountPct,
        startDate: p.startDate,
        endDate: p.endDate,
        createdBy: p.createdBy,
      };
    }
    return null;
  } catch {
    return null;
  }
}

/** Real GET of the one `reservation.<orgId>` ConfigMap key -- `data:
 * null` (not an error) when this org has never committed to a
 * reservation, same honest-absence convention every ConfigMap-backed
 * module in this codebase (getStoredOverage, getOrgSla, ...) already
 * uses. */
export async function getReservation(orgId: string): Promise<K8sResult<CapacityReservation | null>> {
  const cm = await getConfigMap(RESERVATIONS_NAMESPACE, RESERVATIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const raw = cm.data?.data?.[reservationConfigMapKey(orgId)];
  if (!raw) return { ok: true, data: null };
  const parsed = parseStoredReservation(orgId, raw);
  if (!parsed) return { ok: false, error: `corrupt stored capacity reservation for org ${orgId}` };
  return { ok: true, data: parsed };
}

/** Real listing of every org's current reservation record -- used by the
 * expiry sweep (walks every key, same "list the whole ConfigMap, filter
 * client-side" shape lib/orgs.ts's getRegistry already uses since a
 * ConfigMap has no server-side per-key query). */
export async function listReservations(): Promise<K8sResult<CapacityReservation[]>> {
  const cm = await getConfigMap(RESERVATIONS_NAMESPACE, RESERVATIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const reservations: CapacityReservation[] = [];
  for (const [key, raw] of Object.entries(data)) {
    if (!key.startsWith("reservation.")) continue;
    const orgId = key.slice("reservation.".length);
    const parsed = parseStoredReservation(orgId, raw);
    if (parsed) reservations.push(parsed);
  }
  return { ok: true, data: reservations };
}

async function putReservation(reservation: CapacityReservation): Promise<K8sResult<CapacityReservation>> {
  const result = await createOrUpdateConfigMap(RESERVATIONS_NAMESPACE, RESERVATIONS_CONFIGMAP, {
    [reservationConfigMapKey(reservation.orgId)]: JSON.stringify(reservation),
  });
  if (!result.ok) return result;
  return { ok: true, data: reservation };
}

/** Real key removal via an RFC 7386 JSON merge patch that sets the key
 * to `null` -- the standard merge-patch "delete this key" idiom, same
 * `Record<string, string | null>` shape lib/k8s.ts's own
 * patchNamespaceAnnotations already establishes for a null-deletes-the-
 * key merge patch. createOrUpdateConfigMap's own typed helper only
 * accepts `Record<string, string>` (every OTHER ConfigMap-backed module
 * only ever ADDS/overwrites keys, never deletes one), so this calls
 * k8sRequest directly rather than widening that shared helper's type for
 * one caller. */
async function deleteReservationKey(orgId: string): Promise<K8sResult<null>> {
  const result = await k8sRequest<unknown>(
    `/api/v1/namespaces/${encodeURIComponent(RESERVATIONS_NAMESPACE)}/configmaps/${encodeURIComponent(RESERVATIONS_CONFIGMAP)}`,
    "PATCH",
    { data: { [reservationConfigMapKey(orgId)]: null } },
    "application/merge-patch+json",
  );
  if (!result.ok) return result;
  return { ok: true, data: null };
}

/** Real k8s ResourceQuota object name for one namespace -- the exact
 * `${namespace}-quota` convention lib/k8s.ts's own
 * ensureResourceQuotaForTier/createOrUpdateResourceQuota callers already
 * use at provisioning time, so a reservation patches the SAME object the
 * tier ceiling itself lives on, never a second/parallel one. */
export function reservationQuotaName(namespace: string): string {
  return `${namespace}-quota`;
}

/** Real `spec.hard` merge-patch body for a committed reservation. Only
 * the CPU/memory keys are set -- an RFC 7386 merge patch on a nested
 * object is recursive per-key, so `pods` (and any other existing hard
 * key) on the namespace's real ResourceQuota is left completely
 * untouched, same "never a blind full-object PUT" discipline
 * lib/k8s.ts's own createOrUpdateConfigMap header comment documents for
 * ConfigMaps. Cores/GiB round-trip as plain decimal quantity strings
 * ("4", "4.5") / binary-suffix quantity strings ("8Gi") -- the same two
 * real k8s Quantity forms TIER_RESOURCE_QUOTAS itself uses. */
export function committedResourceQuotaHard(
  committedCpuCores: number,
  committedMemoryGi: number,
): Record<string, string> {
  const cpu = String(committedCpuCores);
  const memory = `${committedMemoryGi}Gi`;
  return {
    "requests.cpu": cpu,
    "limits.cpu": cpu,
    "requests.memory": memory,
    "limits.memory": memory,
  };
}

export interface CreateReservationInput {
  orgId: string;
  namespace: string;
  committedCpuCores: number;
  committedMemoryGi: number;
  termMonths: ReservationTermMonths;
  createdBy: string;
}

export type CreateReservationResult =
  | { ok: true; data: CapacityReservation }
  | { ok: false; error: string };

/**
 * Real end-to-end commit: resolves the org's current real Project tier
 * (getOrgProjectTier, the same live-derived source every other
 * tier-aware module in this codebase reads), looks up the real
 * discountPct for (tier, termMonths) from RESERVATION_DISCOUNT_TABLE,
 * raises the namespace's real ResourceQuota.spec.hard to the committed
 * level IMMEDIATELY (patchResourceQuotaHard -- see this module's header
 * comment for why this is the same enforcement primitive, no new k8s
 * verb), then persists the record. The quota patch is applied BEFORE the
 * ConfigMap write so a caller never sees a "committed" record whose
 * headroom was not actually granted; if the quota patch fails, nothing
 * is persisted and the caller gets a real error, never a silently
 * unenforced commitment.
 */
export async function createReservation(input: CreateReservationInput): Promise<CreateReservationResult> {
  if (!Number.isFinite(input.committedCpuCores) || input.committedCpuCores <= 0) {
    return { ok: false, error: "committedCpuCores must be a positive number" };
  }
  if (!Number.isFinite(input.committedMemoryGi) || input.committedMemoryGi <= 0) {
    return { ok: false, error: "committedMemoryGi must be a positive number" };
  }
  if (!isReservationTermMonths(input.termMonths)) {
    return { ok: false, error: "termMonths must be one of the supported commitment terms" };
  }

  const tierResult = await getOrgProjectTier(input.namespace);
  if (!tierResult.ok) return { ok: false, error: tierResult.error };
  const tier = tierResult.data;

  const discountPct = reservationDiscountPct(tier, input.termMonths);

  const hard = committedResourceQuotaHard(input.committedCpuCores, input.committedMemoryGi);
  const quotaResult = await patchResourceQuotaHard(input.namespace, reservationQuotaName(input.namespace), hard);
  if (!quotaResult.ok) return { ok: false, error: quotaResult.error };

  const startDate = new Date();
  const endDate = new Date(startDate);
  endDate.setUTCMonth(endDate.getUTCMonth() + input.termMonths);

  const reservation: CapacityReservation = {
    orgId: input.orgId,
    namespace: input.namespace,
    tier,
    committedCpuCores: input.committedCpuCores,
    committedMemoryGi: input.committedMemoryGi,
    termMonths: input.termMonths,
    discountPct,
    startDate: startDate.toISOString(),
    endDate: endDate.toISOString(),
    createdBy: input.createdBy,
  };

  const stored = await putReservation(reservation);
  if (!stored.ok) return { ok: false, error: stored.error };
  return { ok: true, data: stored.data };
}

/**
 * Real revert-and-clear: patches the namespace's ResourceQuota back down
 * to its real Project tier default (resourceQuotaHardFor -- the exact
 * same table/shape `createOrUpdateResourceQuota` builds at provisioning
 * time) and deletes the `reservation.<orgId>` ConfigMap key. Used both by
 * the owner-gated DELETE route (explicit cancellation) and by
 * `sweepExpiredReservations` below (automatic, scheduled expiry) -- the
 * two real callers of this one revert primitive, never a duplicated
 * revert implementation.
 */
export async function cancelReservation(orgId: string, namespace: string): Promise<K8sResult<null>> {
  const tierResult = await getOrgProjectTier(namespace);
  if (!tierResult.ok) return tierResult;

  const quotaResult = await patchResourceQuotaHard(
    namespace,
    reservationQuotaName(namespace),
    resourceQuotaHardFor(tierResult.data),
  );
  if (!quotaResult.ok) return quotaResult;

  return deleteReservationKey(orgId);
}

/**
 * Real scheduled-expiry sweep -- the fan-out target
 * lib/scheduled-jobs.ts's `createCronJob` pattern (one platform-wide
 * CronJob firing into a real, secret-authenticated internal route, same
 * shape as lib/s3-export-subscription.ts's runDueExportSubscriptions)
 * curls on a recurring schedule. Walks every stored reservation; a
 * reservation whose real `endDate` has passed gets its ResourceQuota
 * reverted to the tier default and its ConfigMap key cleared via
 * cancelReservation -- an active (not-yet-expired) reservation is left
 * completely untouched. One reservation's revert failure never blocks
 * the sweep for any other org, same "one org's failure never blocks the
 * next" posture runDueExportSubscriptions already establishes.
 */
export async function sweepExpiredReservations(): Promise<
  K8sResult<{ expiredOrgIds: string[]; activeOrgIds: string[]; errors: Array<{ orgId: string; error: string }> }>
> {
  const listed = await listReservations();
  if (!listed.ok) return listed;

  const now = Date.now();
  const expiredOrgIds: string[] = [];
  const activeOrgIds: string[] = [];
  const errors: Array<{ orgId: string; error: string }> = [];

  for (const reservation of listed.data) {
    if (Date.parse(reservation.endDate) > now) {
      activeOrgIds.push(reservation.orgId);
      continue;
    }
    const reverted = await cancelReservation(reservation.orgId, reservation.namespace);
    if (!reverted.ok) {
      errors.push({ orgId: reservation.orgId, error: reverted.error });
      continue;
    }
    expiredOrgIds.push(reservation.orgId);
  }

  return { ok: true, data: { expiredOrgIds, activeOrgIds, errors } };
}
