/**
 * Real, hand-maintained in-app changelog / release-notes feed, tagged by
 * the real minimum `ProjectTier` (lib/tiers.ts) each entry's underlying
 * capability is already gated behind in this codebase today.
 *
 * Closes the gap named in this control's own rationale: `TIER_GATED_FLAGS`
 * (lib/tiers.ts), `lib/orgs.ts`'s enterprise-only `setOrgRegion`, and the
 * per-tier `TIER_RESOURCE_QUOTAS`/`SEAT_LIMITS` tables already enforce a
 * real tier ceiling -- but until now a tier-capped org never sees WHY a
 * capability is unavailable, only a silent 403 (or, for capacity limits,
 * nothing at all -- the ceiling is simply hit with no explanation of what
 * unlocks it). This module is the single, static source of truth for
 * "what does the next tier unlock," each entry pointing at the real
 * module/route that already implements and enforces it, so
 * GET /api/orgs/[id]/changelog and app/changelog/page.tsx can turn that
 * existing enforcement into a visible self-serve upsell surface instead
 * of a dead end.
 *
 * Deliberately a fixed, hand-edited array -- not generated from git log
 * or CI -- same "small, hand-curated, reviewed-in-PR list" discipline
 * `TIER_GATED_FLAGS` itself already uses for which flags are gated. Every
 * `minimumTier` below is verified against a real `tierAtLeast(...)` check
 * (or real per-tier table) elsewhere in this codebase -- never an
 * aspirational or roadmap capability. Newest entries are added at the TOP
 * of the array; `id` is a stable, never-reused slug so a client can key a
 * list by it across re-fetches.
 */
import type { ProjectTier } from "@/lib/tiers";

export interface ChangelogEntry {
  id: string;
  /** ISO 8601 date (YYYY-MM-DD) this capability shipped/became real in
   *  this codebase. */
  date: string;
  title: string;
  body: string;
  /** Minimum `ProjectTier` that must be unlocked (via `tierAtLeast`) for
   *  this capability to actually be usable today. */
  minimumTier: ProjectTier;
}

/**
 * Newest first. Every entry below documents a capability that is real
 * and already enforced elsewhere in this codebase -- never a roadmap
 * item or a capability this repo doesn't actually have.
 */
export const CHANGELOG_ENTRIES: ChangelogEntry[] = [
  {
    id: "data-residency-region-pinning",
    date: "2026-08-01",
    title: "Data residency / region pinning",
    body:
      "Pin an org's Projects to a specific node region for data-residency compliance " +
      "(GDPR/data-sovereignty-style requirements). Enforced today by lib/orgs.ts's " +
      "setOrgRegion, which requires this org's real Project tier (getOrgProjectTier) to " +
      "be enterprise before a region pin is accepted -- see PUT /api/orgs/[id]/region.",
    minimumTier: "enterprise",
  },
  {
    id: "resource-quota-3x-enterprise",
    date: "2026-07-15",
    title: "3x compute ResourceQuota ceiling",
    body:
      "Every Project namespace on this tier gets triple the starter tier's pod count, CPU, " +
      "and memory ceiling (15 pods / 1.5 vCPU requested / 9 vCPU limit vs. starter's 5 pods " +
      "/ 500m / 3 vCPU). See TIER_RESOURCE_QUOTAS in lib/tiers.ts, enforced by " +
      "setProjectTier / patchResourceQuotaHard in lib/k8s.ts.",
    minimumTier: "enterprise",
  },
  {
    id: "seat-limit-unlimited",
    date: "2026-06-20",
    title: "Effectively unlimited seats",
    body:
      "Invite as many members as this org needs -- the enterprise tier's seat cap is 9999, " +
      "versus the pro tier's 25-seat limit. See SEAT_LIMITS in lib/tiers.ts, enforced by " +
      "POST /api/orgs/[id]/invites.",
    minimumTier: "enterprise",
  },
  {
    id: "resource-quota-2x-pro",
    date: "2026-05-14",
    title: "2x compute ResourceQuota ceiling",
    body:
      "Every Project namespace on this tier gets double the starter tier's pod count, CPU, " +
      "and memory ceiling (10 pods / 1 vCPU requested / 6 vCPU limit vs. starter's 5 pods / " +
      "500m / 3 vCPU). See TIER_RESOURCE_QUOTAS in lib/tiers.ts.",
    minimumTier: "pro",
  },
  {
    id: "verbose-status-flag",
    date: "2026-05-01",
    title: "Verbose /status diagnostics feature flag",
    body:
      "Enable the verbose-status feature flag to get extended diagnostic detail on the " +
      "live /status endpoint (services/autofde-lab/app.py), instead of the default summary " +
      "response. Gated by TIER_GATED_FLAGS in lib/tiers.ts and enforced in " +
      "app/api/feature-flags/route.ts.",
    minimumTier: "pro",
  },
  {
    id: "seat-limit-25",
    date: "2026-04-20",
    title: "25 included seats",
    body:
      "Invite up to 25 members to this org, up from the starter tier's 5-seat cap. See " +
      "SEAT_LIMITS in lib/tiers.ts, enforced by POST /api/orgs/[id]/invites.",
    minimumTier: "pro",
  },
];
