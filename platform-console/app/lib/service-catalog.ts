/**
 * Real Customer-Facing Service Catalog / Entitlement Matrix (AWS Service
 * Catalog / GCP Console "Enabled APIs" equivalent): closes the gap that
 * an enterprise buyer's procurement or technical evaluator must currently
 * cross-reference lib/tiers.ts, the live `platform-feature-flags`
 * ConfigMap, and support tickets by hand to answer "exactly what
 * capabilities are enabled for us right now". This module assembles that
 * answer server-side, once, from the SAME real sources every other
 * tier-gated route in this codebase already reads -- never a second,
 * divergent copy of a tier check.
 *
 * Deliberately distinct from two existing pages this could be confused
 * with:
 *   - lib/trust-page.ts (`/trust`) publishes aggregate SECURITY POSTURE
 *     (CVE counts, cert/uptime stats) -- no notion of per-org entitlement.
 *   - lib/changelog.ts publishes RELEASE NOTES (what changed over time)
 *     -- no notion of current-state enablement.
 * This module answers neither of those; it answers "what is on, right
 * now, for this org" as a flat, read-only list.
 *
 * Each entry's `enabled`/`limit`/`tierRequiredForUpgrade` is read from
 * the SAME constant the real gate already uses (TIER_RESOURCE_QUOTAS,
 * SEAT_LIMITS, RETENTION_DEFAULT_DAYS/RETENTION_RANGE, SLA_TIER_DEFAULTS,
 * PATCH_SLA_COMMITTED_HOURS, TIER_LIMITS, TIER_GATED_FLAGS/isFlagEntitled)
 * -- this module never re-derives a threshold or invents a new one.
 * Capabilities with no real tier gate anywhere in this codebase today
 * (custom-domain self-service, SAML config surface, egress-IP
 * publication) are listed as `enabled: true` with no
 * `tierRequiredForUpgrade`, reflecting that they are genuinely available
 * to every tier as of this pass -- never fabricated as gated to look more
 * "enterprise".
 */
import { getConfigMap } from "@/lib/k8s";
import { getOrg, getOrgProjectTier, getOrgSla } from "@/lib/orgs";
import {
  DEFAULT_SLA_TIER,
  PATCH_SLA_COMMITTED_HOURS,
  RESERVATION_DISCOUNT_TABLE,
  SEAT_LIMITS,
  SLA_TIER_DEFAULTS,
  TIER_GATED_FLAGS,
  TIER_RESOURCE_QUOTAS,
  isFlagEntitled,
  tierAtLeast,
  type PatchSlaTier,
  type ProjectTier,
} from "@/lib/tiers";
import { RETENTION_DEFAULT_DAYS, RETENTION_RANGE } from "@/lib/backup-retention";
import { TIER_LIMITS, type ApiKeyTier } from "@/lib/rate-limit";
import { PLATFORM_EGRESS_CIDRS } from "@/lib/egress-ips";

const FLAGS_NAMESPACE = "platform-console";
const FLAGS_CONFIGMAP = "platform-feature-flags";

/** ProjectTier -> the ApiKeyTier name lib/rate-limit.ts's TIER_LIMITS is
 * keyed by. Two independently-named axes (see lib/api-keys.ts's header
 * comment: a key's tier reflects the customer's paid plan but is minted
 * per-key, not derived) -- `starter` maps to rate-limit's entry-level
 * `standard` name, `pro`/`enterprise` map 1:1, so the catalog can show
 * the rate ceiling this org's Project tier corresponds to today without
 * inventing a fourth tier name. */
const PROJECT_TIER_TO_API_KEY_TIER: Record<ProjectTier, ApiKeyTier> = {
  starter: "standard",
  pro: "pro",
  enterprise: "enterprise",
};

/** Lowest ProjectTier at which a given ApiKeyTier's ceiling first
 * becomes available, for the catalog's "upgrade to unlock" hint --
 * inverse of PROJECT_TIER_TO_API_KEY_TIER above. */
const API_KEY_TIER_TO_PROJECT_TIER: Record<ApiKeyTier, ProjectTier> = {
  standard: "starter",
  pro: "pro",
  enterprise: "enterprise",
};

export interface ServiceCatalogEntry {
  capabilityKey: string;
  displayName: string;
  enabled: boolean;
  limit?: string;
  tierRequiredForUpgrade?: ProjectTier;
}

export interface ServiceCatalog {
  orgId: string;
  orgName: string;
  projectTier: ProjectTier;
  slaTier: string;
  patchSlaTier: PatchSlaTier | null;
  generatedAt: string;
  entries: ServiceCatalogEntry[];
}

/**
 * Real, org-scoped Service Catalog assembly. Reads the org's live
 * ProjectTier (getOrgProjectTier -- the highest tier among its real
 * Projects, same source app/api/feature-flags/route.ts's entitlement
 * metadata already uses), its contracted SLA tier (getOrgSla), its
 * contracted patch-SLA tier (org.patchSlaTier, may be unset), and the
 * live `platform-feature-flags` ConfigMap -- then assembles one flat
 * list covering every capability this codebase actually gates (or
 * explicitly does not gate) by tier. Fails closed: any k8s read failure
 * is surfaced as an error, never silently defaulted into a fabricated
 * "everything enabled" catalog.
 */
export async function getServiceCatalogForOrg(
  orgId: string,
): Promise<{ ok: true; data: ServiceCatalog } | { ok: false; error: string; status: number }> {
  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return { ok: false, error: orgResult.error, status: 502 };
  }
  if (!orgResult.data) {
    return { ok: false, error: "org not found", status: 404 };
  }
  const org = orgResult.data;

  const tierResult = await getOrgProjectTier(org.namespace);
  if (!tierResult.ok) {
    return { ok: false, error: tierResult.error, status: 502 };
  }
  const projectTier = tierResult.data;

  const slaResult = await getOrgSla(orgId);
  if (!slaResult.ok) {
    return { ok: false, error: slaResult.error, status: 502 };
  }
  const slaTier = slaResult.data?.slaTier ?? DEFAULT_SLA_TIER;
  const patchSlaTier = org.patchSlaTier ?? null;

  const flagsResult = await getConfigMap(FLAGS_NAMESPACE, FLAGS_CONFIGMAP);
  if (!flagsResult.ok) {
    return { ok: false, error: flagsResult.error, status: 502 };
  }
  const rawFlags = flagsResult.data?.data ?? {};

  const entries: ServiceCatalogEntry[] = [];

  // --- Compute / resource quota ceilings (TIER_RESOURCE_QUOTAS) ---
  const quota = TIER_RESOURCE_QUOTAS[projectTier];
  entries.push({
    capabilityKey: "resource-quota",
    displayName: "Namespace resource quota",
    enabled: true,
    limit: `${quota.pods} pods, ${quota.requestsCpu}/${quota.limitsCpu} CPU (req/limit), ${quota.requestsMemory}/${quota.limitsMemory} memory (req/limit)`,
  });

  // --- Seat limit (SEAT_LIMITS) ---
  entries.push({
    capabilityKey: "seats",
    displayName: "User seats",
    enabled: true,
    limit: `${SEAT_LIMITS[projectTier]} seats`,
    tierRequiredForUpgrade: projectTier === "enterprise" ? undefined : "enterprise",
  });

  // --- API rate-limit tier (TIER_LIMITS via rate-limit.ts) ---
  const apiKeyTier = PROJECT_TIER_TO_API_KEY_TIER[projectTier];
  const rateLimit = TIER_LIMITS[apiKeyTier];
  entries.push({
    capabilityKey: "api-rate-limit",
    displayName: "API key rate-limit tier",
    enabled: true,
    limit: `${rateLimit.maxTokens} req / ${rateLimit.fillIntervalMs / 1000}s (per key, "${apiKeyTier}" tier)`,
  });

  // --- Backup retention (RETENTION_DEFAULT_DAYS / RETENTION_RANGE) ---
  const retentionRange = RETENTION_RANGE[projectTier];
  entries.push({
    capabilityKey: "backup-retention",
    displayName: "Backup retention",
    enabled: true,
    limit: `default ${RETENTION_DEFAULT_DAYS[projectTier]} days, up to ${retentionRange.maxDays} days`,
    tierRequiredForUpgrade: projectTier === "enterprise" ? undefined : "enterprise",
  });

  // --- Uptime / support SLA (SLA_TIER_DEFAULTS) ---
  const slaDefaults = SLA_TIER_DEFAULTS[slaTier];
  entries.push({
    capabilityKey: "uptime-sla",
    displayName: "Uptime & support-response SLA",
    enabled: true,
    limit: `${slaDefaults.slaUptimeTargetPct}% uptime target, ${slaDefaults.slaResponseTimeHours}h response ("${slaTier}")`,
  });

  // --- Patch-timeliness SLA (PATCH_SLA_COMMITTED_HOURS) ---
  entries.push({
    capabilityKey: "patch-sla",
    displayName: "Contractual patch-timeliness SLA",
    enabled: patchSlaTier !== null,
    limit: patchSlaTier
      ? `CRITICAL within ${PATCH_SLA_COMMITTED_HOURS[patchSlaTier].CRITICAL}h, HIGH within ${PATCH_SLA_COMMITTED_HOURS[patchSlaTier].HIGH}h ("${patchSlaTier}")`
      : undefined,
  });

  // --- Custom-domain self-service (no tier gate exists in this codebase) ---
  entries.push({
    capabilityKey: "custom-domain-self-service",
    displayName: "Custom domain + TLS self-service",
    enabled: true,
  });

  // --- SSO / SAML config surface (no tier gate exists in this codebase) ---
  entries.push({
    capabilityKey: "sso-saml-config",
    displayName: "SSO / SAML 2.0 configuration surface",
    enabled: true,
  });

  // --- Egress IP publication (no tier gate; static, published to every org) ---
  entries.push({
    capabilityKey: "egress-ip-publication",
    displayName: "Outbound webhook IP allowlist publication",
    enabled: true,
    limit: PLATFORM_EGRESS_CIDRS.join(", "),
  });

  // --- Committed-use capacity reservation discount (RESERVATION_DISCOUNT_TABLE) ---
  const discountRow = RESERVATION_DISCOUNT_TABLE[projectTier];
  entries.push({
    capabilityKey: "capacity-reservation-discount",
    displayName: "Committed-use capacity reservation discount",
    enabled: true,
    limit: `up to ${discountRow[36]}% (36mo term)`,
  });

  // --- Live feature flags (platform-feature-flags ConfigMap + TIER_GATED_FLAGS) ---
  const flagKeys = new Set<string>([...Object.keys(rawFlags), ...Object.keys(TIER_GATED_FLAGS)]);
  for (const key of Array.from(flagKeys).sort()) {
    const requiredTier = TIER_GATED_FLAGS[key] ?? "starter";
    const entitled = isFlagEntitled(projectTier, key);
    const liveEnabled = rawFlags[key] === "true";
    entries.push({
      capabilityKey: `feature-flag:${key}`,
      displayName: `Feature flag: ${key}`,
      enabled: entitled && liveEnabled,
      tierRequiredForUpgrade: entitled ? undefined : requiredTier,
    });
  }

  return {
    ok: true,
    data: {
      orgId,
      orgName: org.name,
      projectTier,
      slaTier,
      patchSlaTier,
      generatedAt: new Date().toISOString(),
      entries,
    },
  };
}
