/**
 * Real Reserved-Capacity Secondary Marketplace (AWS Reserved Instance
 * Marketplace equivalent): the capability that closes the gap
 * lib/capacity-reservations.ts's own header comment leaves open --
 * an org that over-committed to a Committed-Use Capacity Reservation has
 * no way to recover that sunk cost today; the ResourceQuota headroom it
 * paid for just sits idle until the reservation's real `endDate` and
 * `sweepExpiredReservations` claws it back for free. This module lets
 * that org list some of its own reservation's UNUSED committed capacity
 * for another org to buy for the remainder of the term, at a real
 * mid-point price (validated by `validateResalePrice` below to sit
 * between the seller's own sunk discounted cost and the standard/
 * overage cost a buyer would otherwise pay), and takes a real platform
 * transaction fee on every sale (`computeMarketplaceFeeLineItem`,
 * lib/invoice-preview.ts) -- the exact lever that reduces the CFO
 * objection currently capping how large a reservation buyers are
 * willing to make in the first place.
 *
 * Units: every listing is denominated in whole "units", where one unit
 * is `UNIT_CPU_CORES` (1) committed CPU core PLUS its proportional share
 * of the seller reservation's own `committedMemoryGi` at the moment the
 * listing is created (`memoryGiPerUnit = committedMemoryGi /
 * committedCpuCores`, frozen onto the listing record so a later change
 * to the seller's remaining committed ratio never silently reprices an
 * already-listed unit). CPU and memory are never sold as two
 * independently-priced things -- exactly how the underlying
 * ResourceQuota ceiling itself always moves (both keys in one merge
 * patch, lib/capacity-reservations.ts's own `committedResourceQuotaHard`).
 *
 * Ownership transfer mechanics: buying `units` of a listing calls the
 * SAME real `patchResourceQuotaHard` (lib/k8s.ts) RFC 7386 merge-patch
 * primitive TWICE -- once to lower the seller namespace's
 * `${namespace}-quota` hard ceiling by the sold amount, once to raise
 * the buyer namespace's own `${namespace}-quota` hard ceiling by the
 * same amount -- no new k8s verb, the exact same enforcement primitive
 * `createReservation`/`cancelReservation` already use. The seller's own
 * `CapacityReservation.committedCpuCores`/`committedMemoryGi` record is
 * reduced by the same amount so a sold unit is never double-counted as
 * still "the seller's committed capacity" after the sale, and the
 * buyer's headroom is granted directly against their real ResourceQuota
 * -- a buyer does NOT get a new `CapacityReservation` record of their
 * own (they bought raised headroom for the remainder of the seller's
 * term, not a fresh forward commitment with its own discount table
 * entry); `sweepExpiredReservations` reverting the SELLER's reservation
 * to the tier default at the seller's own `endDate` therefore also
 * reverts the now-sold-off portion at the same moment -- exactly the
 * real "the capacity you bought secondhand still expires when the
 * original term does" AWS RI Marketplace behavior this mirrors.
 *
 * Storage: the SAME `platform-console-capacity-reservations` ConfigMap
 * lib/capacity-reservations.ts already owns, one `marketplace.<listingId>`
 * key per listing -- the exact "no new k8s resource kind, one key per
 * record, JSON value" convention that module's own header comment
 * documents, just a second key prefix inside the same ConfigMap rather
 * than a new one. A listing's own key is written once at creation and
 * then updated in place as units sell (never deleted) -- `purchases`
 * accumulates a real, append-only history of every real sale against it,
 * so "listings/history" really is the same stored record, not two
 * separate stores that could drift.
 */
import {
  createOrUpdateConfigMap,
  getConfigMap,
  getResourceQuotaByName,
  k8sRequest,
  patchResourceQuotaHard,
  quantityToMiB,
  quantityToMillicores,
  type K8sResult,
} from "@/lib/k8s";
import {
  RESERVATIONS_CONFIGMAP,
  RESERVATIONS_NAMESPACE,
  putReservationRecord,
  reservationQuotaName,
  type CapacityReservation,
} from "@/lib/capacity-reservations";
import { getReservation } from "@/lib/capacity-reservations";
import { ILLUSTRATIVE_RATES } from "@/lib/invoice-preview";

/** One unit of resale capacity is always exactly 1 committed CPU core --
 * see this module's header comment for why memory rides along
 * proportionally instead of being priced/sold separately. */
export const UNIT_CPU_CORES = 1;

const MARKETPLACE_KEY_PREFIX = "marketplace.";

function listingConfigMapKey(listingId: string): string {
  return `${MARKETPLACE_KEY_PREFIX}${listingId}`;
}

export interface ResaleListingPurchase {
  buyerOrgId: string;
  buyerNamespace: string;
  units: number;
  pricePerUnit: number;
  purchaseAmount: number;
  platformFeePct: number;
  platformFee: number;
  purchasedAt: string;
  purchasedBy: string;
}

export type ResaleListingStatus = "open" | "sold_out" | "cancelled";

export interface ResaleListing {
  listingId: string;
  sellerOrgId: string;
  sellerNamespace: string;
  /** Reservation term end this listing's sale can never outlive -- copied
   * from the seller `CapacityReservation.endDate` at listing time so a
   * listing's own record carries proof of the remaining-term validation
   * `createResaleListing` performed, independent of the seller
   * reservation's later state. */
  reservationEndDate: string;
  memoryGiPerUnit: number;
  pricePerUnit: number;
  unitsListedOriginal: number;
  unitsAvailable: number;
  status: ResaleListingStatus;
  createdAt: string;
  createdBy: string;
  purchases: ResaleListingPurchase[];
}

function parseStoredListing(listingId: string, raw: string): ResaleListing | null {
  try {
    const p = JSON.parse(raw) as Partial<ResaleListing>;
    if (
      typeof p.sellerOrgId === "string" &&
      typeof p.sellerNamespace === "string" &&
      typeof p.reservationEndDate === "string" &&
      typeof p.memoryGiPerUnit === "number" &&
      typeof p.pricePerUnit === "number" &&
      typeof p.unitsListedOriginal === "number" &&
      typeof p.unitsAvailable === "number" &&
      (p.status === "open" || p.status === "sold_out" || p.status === "cancelled") &&
      typeof p.createdAt === "string" &&
      typeof p.createdBy === "string" &&
      Array.isArray(p.purchases)
    ) {
      return {
        listingId,
        sellerOrgId: p.sellerOrgId,
        sellerNamespace: p.sellerNamespace,
        reservationEndDate: p.reservationEndDate,
        memoryGiPerUnit: p.memoryGiPerUnit,
        pricePerUnit: p.pricePerUnit,
        unitsListedOriginal: p.unitsListedOriginal,
        unitsAvailable: p.unitsAvailable,
        status: p.status,
        createdAt: p.createdAt,
        createdBy: p.createdBy,
        purchases: p.purchases as ResaleListingPurchase[],
      };
    }
    return null;
  } catch {
    return null;
  }
}

/** Real GET of one `marketplace.<listingId>` ConfigMap key -- `data: null`
 * (not an error) when no listing with this id exists, same honest-
 * absence convention lib/capacity-reservations.ts's own `getReservation`
 * already establishes. */
export async function getListing(listingId: string): Promise<K8sResult<ResaleListing | null>> {
  const cm = await getConfigMap(RESERVATIONS_NAMESPACE, RESERVATIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const raw = cm.data?.data?.[listingConfigMapKey(listingId)];
  if (!raw) return { ok: true, data: null };
  const parsed = parseStoredListing(listingId, raw);
  if (!parsed) return { ok: false, error: `corrupt stored marketplace listing ${listingId}` };
  return { ok: true, data: parsed };
}

/** Real listing of every `marketplace.*` key in the shared ConfigMap --
 * same "walk the whole ConfigMap, filter client-side by key prefix"
 * shape `listReservations` already uses for its own `reservation.*`
 * prefix in the SAME ConfigMap. */
export async function listListings(): Promise<K8sResult<ResaleListing[]>> {
  const cm = await getConfigMap(RESERVATIONS_NAMESPACE, RESERVATIONS_CONFIGMAP);
  if (!cm.ok) return cm;
  const data = cm.data?.data ?? {};
  const listings: ResaleListing[] = [];
  for (const [key, raw] of Object.entries(data)) {
    if (!key.startsWith(MARKETPLACE_KEY_PREFIX)) continue;
    const listingId = key.slice(MARKETPLACE_KEY_PREFIX.length);
    const parsed = parseStoredListing(listingId, raw);
    if (parsed) listings.push(parsed);
  }
  return { ok: true, data: listings };
}

async function putListing(listing: ResaleListing): Promise<K8sResult<ResaleListing>> {
  const result = await createOrUpdateConfigMap(RESERVATIONS_NAMESPACE, RESERVATIONS_CONFIGMAP, {
    [listingConfigMapKey(listing.listingId)]: JSON.stringify(listing),
  });
  if (!result.ok) return result;
  return { ok: true, data: listing };
}

/**
 * Real per-unit price bounds for the remaining term of `reservation`:
 * `overageCeiling` is what a buyer would pay for that same capacity at
 * the STANDARD, undiscounted rate (lib/invoice-preview.ts's
 * ILLUSTRATIVE_RATES -- the same rate lib/overage-billing.ts already
 * bills usage above a tier's default entitlement at, so this is a real
 * "spot/overage" price, not a fabricated one); `sunkCostFloor` is what
 * the seller ITSELF already locked in for that same capacity at its own
 * `discountPct` -- the real sunk cost a rational seller should never
 * sell below. A real "mid-point discount" listing prices strictly
 * between the two: cheaper than buying it themselves at the standard
 * rate (or the buyer has no reason to use the marketplace at all),
 * pricier than what it cost the seller to reserve in the first place (or
 * the seller loses more than the sunk-cost floor already represents).
 * Both bounds are computed over the SAME remaining-term hours
 * (`reservation.endDate` minus now), so a listing created near a
 * reservation's own expiry is bounded by a proportionally smaller price
 * window, never a stale full-term number.
 */
export function resalePriceBounds(
  reservation: CapacityReservation,
  memoryGiPerUnit: number,
  now: number = Date.now(),
): { hoursRemaining: number; sunkCostFloor: number; overageCeiling: number } {
  const hoursRemaining = Math.max(0, (Date.parse(reservation.endDate) - now) / (1000 * 60 * 60));
  const standardUnitCostPerHour =
    UNIT_CPU_CORES * ILLUSTRATIVE_RATES.cpuPerCoreHour + memoryGiPerUnit * ILLUSTRATIVE_RATES.memoryPerGiBHour;
  const overageCeiling = standardUnitCostPerHour * hoursRemaining;
  const sunkCostFloor = overageCeiling * (1 - reservation.discountPct / 100);
  return { hoursRemaining, sunkCostFloor, overageCeiling };
}

export interface CreateListingInput {
  sellerOrgId: string;
  sellerNamespace: string;
  units: number;
  pricePerUnit: number;
  createdBy: string;
}

export type CreateListingResult =
  | { ok: true; data: ResaleListing }
  | { ok: false; error: string };

/**
 * Real end-to-end listing creation: resolves the seller's own active
 * `CapacityReservation` (must exist and have a real, unexpired
 * `endDate` -- an expired reservation has already been swept and has no
 * committed capacity left to list), computes how many CPU-core units of
 * it are ALREADY listed (`reservation.listedForResale.unitsAvailable`,
 * so a seller can never list more of their own committed capacity than
 * they actually still hold across every open listing combined), and
 * validates `pricePerUnit` against `resalePriceBounds`. Only on every
 * check passing does this create the `marketplace.<listingId>` record
 * AND write the seller reservation's own `listedForResale` summary back
 * (`putReservationRecord`) -- the two writes the spec's `listedForResale`
 * field and this module's own listing record both depend on staying in
 * sync, done as the last two calls once nothing can fail, mirroring
 * `createReservation`'s own "quota patch before the record write" fail-
 * closed ordering discipline (nothing here mutates real k8s state --
 * only the ConfigMap-stored discovery of what's for sale -- so ordering
 * here is about never advertising more than is actually still owned,
 * not about a k8s quota primitive).
 */
export async function createResaleListing(input: CreateListingInput): Promise<CreateListingResult> {
  if (!Number.isFinite(input.units) || input.units <= 0 || !Number.isInteger(input.units)) {
    return { ok: false, error: "units must be a positive whole number of CPU-core-equivalent units" };
  }
  if (!Number.isFinite(input.pricePerUnit) || input.pricePerUnit <= 0) {
    return { ok: false, error: "pricePerUnit must be a positive number" };
  }

  const reservationResult = await getReservation(input.sellerOrgId);
  if (!reservationResult.ok) return { ok: false, error: reservationResult.error };
  const reservation = reservationResult.data;
  if (!reservation) {
    return { ok: false, error: "seller org has no capacity reservation to list" };
  }
  if (reservation.namespace !== input.sellerNamespace) {
    return { ok: false, error: "seller namespace does not match the org's own reservation namespace" };
  }
  if (Date.parse(reservation.endDate) <= Date.now()) {
    return { ok: false, error: "seller reservation has already expired -- nothing left to list" };
  }
  if (reservation.committedCpuCores < UNIT_CPU_CORES) {
    return { ok: false, error: "seller reservation commits less than one whole CPU-core unit -- nothing to list" };
  }

  const alreadyListedUnits = reservation.listedForResale?.unitsAvailable ?? 0;
  const totalCommittedUnits = Math.floor(reservation.committedCpuCores / UNIT_CPU_CORES);
  const unitsStillOwned = totalCommittedUnits - alreadyListedUnits;
  if (input.units > unitsStillOwned) {
    return {
      ok: false,
      error: `cannot list ${input.units} unit(s): only ${unitsStillOwned} unlisted unit(s) remain on this reservation`,
    };
  }

  const memoryGiPerUnit = reservation.committedMemoryGi / reservation.committedCpuCores;
  const bounds = resalePriceBounds(reservation, memoryGiPerUnit);
  if (input.pricePerUnit < bounds.sunkCostFloor || input.pricePerUnit > bounds.overageCeiling) {
    return {
      ok: false,
      error: `pricePerUnit must sit between the seller's own sunk reservation cost ($${bounds.sunkCostFloor.toFixed(2)}) and the standard/overage cost for the remaining term ($${bounds.overageCeiling.toFixed(2)})`,
    };
  }

  const listingId = `resale-${reservation.orgId}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  const listing: ResaleListing = {
    listingId,
    sellerOrgId: input.sellerOrgId,
    sellerNamespace: input.sellerNamespace,
    reservationEndDate: reservation.endDate,
    memoryGiPerUnit,
    pricePerUnit: input.pricePerUnit,
    unitsListedOriginal: input.units,
    unitsAvailable: input.units,
    status: "open",
    createdAt: new Date().toISOString(),
    createdBy: input.createdBy,
    purchases: [],
  };

  const storedListing = await putListing(listing);
  if (!storedListing.ok) return { ok: false, error: storedListing.error };

  const updatedReservation: CapacityReservation = {
    ...reservation,
    listedForResale: {
      pricePerUnit: input.pricePerUnit,
      unitsAvailable: alreadyListedUnits + input.units,
    },
  };
  const storedReservation = await putReservationRecord(updatedReservation);
  if (!storedReservation.ok) return { ok: false, error: storedReservation.error };

  return { ok: true, data: storedListing.data };
}

export interface BuyListingInput {
  listingId: string;
  buyerOrgId: string;
  buyerNamespace: string;
  units: number;
  purchasedBy: string;
  platformFeePct: number;
}

export interface BuyListingResultData {
  listing: ResaleListing;
  purchase: ResaleListingPurchase;
}

export type BuyListingResult =
  | { ok: true; data: BuyListingResultData }
  | { ok: false; error: string };

/**
 * Real cpu-core/Gi-memory delta patch for one namespace's
 * `${namespace}-quota` ResourceQuota: reads the object's real CURRENT
 * `spec.hard` (`getResourceQuotaByName`), adds `deltaCpuCores`/
 * `deltaMemoryGi` (negative to shrink, positive to grow) to the
 * `requests.*`/`limits.*` pair, and patches the result back via the
 * SAME `patchResourceQuotaHard` merge-patch primitive every other quota
 * mutation in this codebase already uses. A missing ResourceQuota object
 * (namespace provisioned before one existed, or `getResourceQuotaByName`
 * itself erroring) is a real, disclosed failure here -- a marketplace
 * sale never fabricates a ceiling to patch against.
 */
async function applyQuotaDelta(
  namespace: string,
  deltaCpuCores: number,
  deltaMemoryGi: number,
): Promise<K8sResult<null>> {
  const quotaName = reservationQuotaName(namespace);
  const existing = await getResourceQuotaByName(namespace, quotaName);
  if (!existing.ok) return existing;
  if (!existing.data) {
    return { ok: false, error: `namespace ${namespace} has no ${quotaName} ResourceQuota to adjust` };
  }
  const hard = existing.data.spec?.hard ?? {};
  const currentCpuCores = (quantityToMillicores(hard["limits.cpu"]) ?? 0) / 1000;
  const currentRequestCpuCores = (quantityToMillicores(hard["requests.cpu"]) ?? 0) / 1000;
  const currentMemoryGi = (quantityToMiB(hard["limits.memory"]) ?? 0) / 1024;
  const currentRequestMemoryGi = (quantityToMiB(hard["requests.memory"]) ?? 0) / 1024;

  const nextCpuCores = Math.max(0, currentCpuCores + deltaCpuCores);
  const nextRequestCpuCores = Math.max(0, currentRequestCpuCores + deltaCpuCores);
  const nextMemoryGi = Math.max(0, currentMemoryGi + deltaMemoryGi);
  const nextRequestMemoryGi = Math.max(0, currentRequestMemoryGi + deltaMemoryGi);

  return patchResourceQuotaHard(namespace, quotaName, {
    "limits.cpu": String(nextCpuCores),
    "requests.cpu": String(nextRequestCpuCores),
    "limits.memory": `${nextMemoryGi}Gi`,
    "requests.memory": `${nextRequestMemoryGi}Gi`,
  });
}

/**
 * Real end-to-end purchase: validates the listing is `open` with enough
 * `unitsAvailable`, re-reads the seller's own current
 * `CapacityReservation` (never trusts a stale in-memory copy), then
 * performs the transfer in this order --
 *
 *   1. Lower the seller namespace's ResourceQuota by the sold units'
 *      real cpu/memory amount (`applyQuotaDelta`, negative delta).
 *   2. Raise the buyer namespace's ResourceQuota by the SAME amount
 *      (`applyQuotaDelta`, positive delta) -- steps 1 and 2 are the two
 *      real `patchResourceQuotaHard` calls this capability's own spec
 *      names.
 *   3. Only once BOTH quota patches succeed does this persist the
 *      seller's reduced `committedCpuCores`/`committedMemoryGi` and
 *      `listedForResale.unitsAvailable`, and the listing's own
 *      `unitsAvailable`/`purchases` -- so a k8s-side failure in step 1
 *      or 2 never leaves a ConfigMap record claiming a sale that didn't
 *      actually move real headroom, same fail-closed ordering
 *      `createReservation` already establishes for quota-then-record.
 *
 * If step 2 (granting the buyer) fails after step 1 (debiting the
 * seller) already succeeded, this makes one real best-effort attempt to
 * revert step 1 before returning the error, so a failed purchase does
 * not leave the seller permanently short capacity it never actually
 * sold; that revert attempt's own failure is folded into the returned
 * error message rather than silently swallowed, so an operator can see a
 * namespace needs manual reconciliation instead of the failure vanishing.
 */
export async function buyResaleListing(input: BuyListingInput): Promise<BuyListingResult> {
  if (!Number.isFinite(input.units) || input.units <= 0 || !Number.isInteger(input.units)) {
    return { ok: false, error: "units must be a positive whole number of CPU-core-equivalent units" };
  }

  const listingResult = await getListing(input.listingId);
  if (!listingResult.ok) return { ok: false, error: listingResult.error };
  const listing = listingResult.data;
  if (!listing) return { ok: false, error: "listing not found" };
  if (listing.status !== "open") return { ok: false, error: `listing is ${listing.status}, not open` };
  if (input.units > listing.unitsAvailable) {
    return { ok: false, error: `only ${listing.unitsAvailable} unit(s) remain available on this listing` };
  }
  if (listing.sellerOrgId === input.buyerOrgId) {
    return { ok: false, error: "an org cannot buy its own resale listing" };
  }
  if (Date.parse(listing.reservationEndDate) <= Date.now()) {
    return { ok: false, error: "the underlying reservation's term has already ended" };
  }

  const reservationResult = await getReservation(listing.sellerOrgId);
  if (!reservationResult.ok) return { ok: false, error: reservationResult.error };
  const reservation = reservationResult.data;
  if (!reservation) return { ok: false, error: "seller no longer has an active reservation to fulfill this sale from" };

  const deltaCpuCores = input.units * UNIT_CPU_CORES;
  const deltaMemoryGi = input.units * listing.memoryGiPerUnit;
  if (reservation.committedCpuCores < deltaCpuCores || reservation.committedMemoryGi < deltaMemoryGi) {
    return { ok: false, error: "seller reservation no longer commits enough capacity to fulfill this sale" };
  }

  const sellerDebit = await applyQuotaDelta(listing.sellerNamespace, -deltaCpuCores, -deltaMemoryGi);
  if (!sellerDebit.ok) return { ok: false, error: `debiting seller quota: ${sellerDebit.error}` };

  const buyerCredit = await applyQuotaDelta(input.buyerNamespace, deltaCpuCores, deltaMemoryGi);
  if (!buyerCredit.ok) {
    const revert = await applyQuotaDelta(listing.sellerNamespace, deltaCpuCores, deltaMemoryGi);
    const revertNote = revert.ok
      ? "seller debit was reverted"
      : `seller debit revert ALSO FAILED (${revert.error}) -- manual reconciliation required`;
    return { ok: false, error: `crediting buyer quota: ${buyerCredit.error} (${revertNote})` };
  }

  const purchaseAmount = input.units * listing.pricePerUnit;
  const platformFee = purchaseAmount * (input.platformFeePct / 100);
  const purchase: ResaleListingPurchase = {
    buyerOrgId: input.buyerOrgId,
    buyerNamespace: input.buyerNamespace,
    units: input.units,
    pricePerUnit: listing.pricePerUnit,
    purchaseAmount,
    platformFeePct: input.platformFeePct,
    platformFee,
    purchasedAt: new Date().toISOString(),
    purchasedBy: input.purchasedBy,
  };

  const remainingUnits = listing.unitsAvailable - input.units;
  const updatedListing: ResaleListing = {
    ...listing,
    unitsAvailable: remainingUnits,
    status: remainingUnits <= 0 ? "sold_out" : "open",
    purchases: [...listing.purchases, purchase],
  };
  const storedListing = await putListing(updatedListing);
  if (!storedListing.ok) return { ok: false, error: storedListing.error };

  const remainingListedUnits = Math.max(0, (reservation.listedForResale?.unitsAvailable ?? 0) - input.units);
  const updatedReservation: CapacityReservation = {
    ...reservation,
    committedCpuCores: reservation.committedCpuCores - deltaCpuCores,
    committedMemoryGi: reservation.committedMemoryGi - deltaMemoryGi,
    ...(remainingListedUnits > 0
      ? { listedForResale: { pricePerUnit: listing.pricePerUnit, unitsAvailable: remainingListedUnits } }
      : {}),
  };
  // Explicit delete of a now-fully-sold `listedForResale` field, since a
  // spread above only ever ADDS/overwrites the key, never removes it --
  // same "an object literal can't unset a key" reasoning that motivates
  // the null-merge-patch idiom this module's sibling deleteReservationKey
  // uses at the k8s layer.
  if (remainingListedUnits <= 0) delete updatedReservation.listedForResale;

  const storedReservation = await putReservationRecord(updatedReservation);
  if (!storedReservation.ok) return { ok: false, error: storedReservation.error };

  return { ok: true, data: { listing: storedListing.data, purchase } };
}

// Re-exported so route handlers can build the seller/buyer namespace's
// real ResourceQuota object name (`${namespace}-quota`) the exact same
// way lib/capacity-reservations.ts's own routes already do, without a
// second, possibly-drifting definition of the convention.
export { RESERVATIONS_CONFIGMAP, RESERVATIONS_NAMESPACE, k8sRequest };
