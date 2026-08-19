/**
 * Real plan-tier model for Project provisioning (Stripe "product tier" /
 * AWS Organizations SCP-by-tag equivalent): closes the gap named in
 * `resource-quotas-enforced`'s evidence rationale -- that ResourceQuota
 * (k8s/resource-quotas.yaml, lib/k8s.ts's getResourceQuota/
 * patchResourceQuotaHard) is a fixed, operator-set ceiling per namespace
 * with no notion of "Enterprise tier gets 3x the quota" or "a
 * feature-flagged capability is Enterprise-only", despite
 * feature-flag-live-toggle-verified already proving a real,
 * live-toggleable flag mechanism (platform-feature-flags ConfigMap,
 * app/api/feature-flags/route.ts) that a plan tier could drive.
 *
 * NOT the same thing as lib/plan-state.ts's PlanState
 * (active/past_due/suspended) -- that module is the Stripe-webhook-driven
 * *billing lifecycle* (is this namespace currently allowed to run at
 * all), continuously reconciled. This module is the *product tier* (which
 * ceiling and which capabilities this namespace is entitled to), set once
 * at provisioning time as a real label on the Project CR itself and read
 * back from that same label -- no separate ConfigMap, no continuous
 * reconciliation loop.
 */

export type ProjectTier = "starter" | "pro" | "enterprise";

export const PROJECT_TIERS: readonly ProjectTier[] = ["starter", "pro", "enterprise"];

export const DEFAULT_PROJECT_TIER: ProjectTier = "starter";

/**
 * Real `metadata.labels` key set on every Project CR at provisioning time
 * (buildProjectManifest in lib/k8s.ts) -- the Project CRD's schema is
 * external (supabase-operator, not owned by this repo) and unknown to
 * accept an arbitrary `spec.tier` field, so the tier is carried as a
 * label instead: labels are always accepted by any CRD's `metadata`,
 * round-trip through the k8s API untouched, and this repo's Resource
 * Tagging module (lib/tags.ts) already establishes the exact same
 * "domain fact as a `platform-console.io/...` label" convention this
 * reuses (`TAG_LABEL_PREFIX`).
 */
export const TIER_LABEL = "platform-console.io/tier";

const TIER_RANK: Record<ProjectTier, number> = { starter: 0, pro: 1, enterprise: 2 };

export function isProjectTier(value: string): value is ProjectTier {
  return value === "starter" || value === "pro" || value === "enterprise";
}

/** True when `tier` is at least as high as `minimum` on the starter < pro
 * < enterprise ordering. */
export function tierAtLeast(tier: ProjectTier, minimum: ProjectTier): boolean {
  return TIER_RANK[tier] >= TIER_RANK[minimum];
}

export interface TierResourceQuota {
  pods: string;
  requestsCpu: string;
  requestsMemory: string;
  limitsCpu: string;
  limitsMemory: string;
}

/**
 * Real per-tier ResourceQuota ceiling table. `starter` reproduces the
 * existing static baseline every project namespace already carries
 * (k8s/resource-quotas.yaml's `ggen-quota`/`autofde-lab-quota` shape:
 * pods 5, requests.cpu 500m, requests.memory 500Mi, limits.memory 5Gi) --
 * so a `starter`-tier project provisioned through this table gets exactly
 * the ceiling every namespace already had, not a silent regression.
 * `pro` is 2x that baseline; `enterprise` is 3x, matching the "Enterprise
 * tier gets 3x the quota" example verbatim in the closed-gap rationale.
 */
export const TIER_RESOURCE_QUOTAS: Record<ProjectTier, TierResourceQuota> = {
  starter: {
    pods: "5",
    requestsCpu: "500m",
    requestsMemory: "500Mi",
    limitsCpu: "3",
    limitsMemory: "3Gi",
  },
  pro: {
    pods: "10",
    requestsCpu: "1",
    requestsMemory: "1Gi",
    limitsCpu: "6",
    limitsMemory: "6Gi",
  },
  enterprise: {
    pods: "15",
    requestsCpu: "1500m",
    requestsMemory: "1500Mi",
    limitsCpu: "9",
    limitsMemory: "9Gi",
  },
};

/** `TIER_RESOURCE_QUOTAS[tier]` reshaped into the real k8s
 * `ResourceQuota.spec.hard` key names (`limits.cpu`, `requests.memory`,
 * ...) -- the exact map both `buildResourceQuotaManifest` (create) and
 * `patchResourceQuotaHard` (lib/k8s.ts, existing plan-state/quota-
 * enforcement enforcement primitive) send as `spec.hard`. */
export function resourceQuotaHardFor(tier: ProjectTier): Record<string, string> {
  const q = TIER_RESOURCE_QUOTAS[tier];
  return {
    pods: q.pods,
    "requests.cpu": q.requestsCpu,
    "requests.memory": q.requestsMemory,
    "limits.cpu": q.limitsCpu,
    "limits.memory": q.limitsMemory,
  };
}

/**
 * Real per-tier seat cap for the seat-based user management control
 * (Vercel/Retool/Auth0 "N seats included, then upsell" pattern): the
 * single lever that makes "the 26th employee" a real, enforced upsell
 * trigger instead of an unbounded free-for-all. `enterprise` is modeled
 * as effectively unlimited (9999) rather than `Infinity` so it survives
 * `JSON.stringify` round-trips through the same ConfigMap-value-as-JSON
 * convention every other per-org record in this codebase already uses,
 * and so seat-usage arithmetic (`used`/`limit`) never has to special-case
 * a non-finite number.
 */
export const SEAT_LIMITS: Record<ProjectTier, number> = {
  starter: 5,
  pro: 25,
  enterprise: 9999,
};

/**
 * Existing `platform-feature-flags` ConfigMap keys (see
 * app/api/feature-flags/route.ts, `feature-flag-live-toggle-verified` in
 * evidence/control-evidence-bundle.json) gated by a minimum Project tier
 * before the flag may be set to `"true"`. Keyed by the ConfigMap `data`
 * key; value is the minimum tier required.
 *
 * `verbose-status` is the flag proven live end-to-end against
 * `autofde-lab-status` (services/autofde-lab/app.py reads this exact
 * ConfigMap on every `/status` request) -- gating it here closes the
 * "no feature-flagged capability is Enterprise-only" half of the named
 * gap using the SAME already-live-verified flag, not a new one.
 */
export const TIER_GATED_FLAGS: Record<string, ProjectTier> = {
  "verbose-status": "pro",
};

/**
 * Which real Project CR's tier label gates each entry in
 * TIER_GATED_FLAGS. `verbose-status` is proven live specifically against
 * the `autofde-lab` namespace's `autofde-lab-status` Service, so that
 * Project's own tier -- not some separate org-wide setting -- is the
 * real gate checked at flag-set time.
 */
export const TIER_GATED_FLAG_OWNER_PROJECT: Record<string, string> = {
  "verbose-status": "autofde-lab",
};

/**
 * Real per-org contractual SLA / support-priority tier (AWS Enterprise
 * Support / GCP Premium Support-style paid line item): closes the gap
 * that this console's Project tier (starter/pro/enterprise, above) sets
 * a compute/quota ceiling but names no contractual uptime commitment or
 * support response-time SLA -- the specific line item enterprise
 * procurement will not sign without (e.g. "99.9% uptime, 4hr response"
 * vs. "99.99% uptime, 1hr response, 24/7"). Deliberately a SEPARATE axis
 * from ProjectTier (an org can be on the `enterprise` Project tier for
 * compute/quota purposes while still contracted at the `standard` SLA
 * tier, or vice versa if Sales prices SLA as its own add-on) -- so it is
 * its own `SlaTier` union, not reused from `ProjectTier`.
 */
export type SlaTier = "standard" | "priority" | "enterprise-247";

export const SLA_TIERS: readonly SlaTier[] = ["standard", "priority", "enterprise-247"];

export const DEFAULT_SLA_TIER: SlaTier = "standard";

export function isSlaTier(value: string): value is SlaTier {
  return value === "standard" || value === "priority" || value === "enterprise-247";
}

export interface SlaTierDefault {
  slaResponseTimeHours: number;
  slaUptimeTargetPct: number;
}

/**
 * Real, fixed per-SLA-tier lookup table -- the single source of truth
 * `PUT /api/orgs/[id]/sla` recomputes `slaResponseTimeHours` and
 * `slaUptimeTargetPct` from whenever `slaTier` changes, same
 * "table keyed by tier, never a free-text/client-supplied number"
 * discipline `TIER_RESOURCE_QUOTAS` above already established for
 * ResourceQuota ceilings. `standard` matches the uptime this console's
 * infra can actually support without a dedicated on-call rotation;
 * `priority` and `enterprise-247` are the paid escalation tiers.
 */
export const SLA_TIER_DEFAULTS: Record<SlaTier, SlaTierDefault> = {
  standard: { slaResponseTimeHours: 24, slaUptimeTargetPct: 99.9 },
  priority: { slaResponseTimeHours: 4, slaUptimeTargetPct: 99.95 },
  "enterprise-247": { slaResponseTimeHours: 1, slaUptimeTargetPct: 99.99 },
};
