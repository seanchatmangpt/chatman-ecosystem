/**
 * Real environment-promotion model for a Project (dev -> staging -> prod) --
 * closes the gap named in this capability's evidence rationale: this repo
 * already has a real, reusable maker-checker primitive
 * (requireApproval, lib/approval-workflow.ts, proven for quota.override,
 * backup.retention.change, and freeze.override) and real per-tier
 * ResourceQuota ceilings (lib/tiers.ts), but no notion of environment on a
 * Project at all -- so "promote this staging deploy to prod" has never had
 * a governed path, the base SOC2 CC8 change-management control (same
 * family as the already-built freeze windows, lib/freeze-windows.ts) every
 * Fortune-5 platform buyer's procurement checklist requires by name.
 *
 * Same `metadata.labels` convention lib/tiers.ts's TIER_LABEL already
 * documents: the real `projects.core.supabase.io` CRD schema is external
 * (supabase-operator, not owned by this repo) and not known to accept an
 * arbitrary `spec.environment` field, so the environment is carried as a
 * label instead -- labels are always accepted by any CRD's `metadata`,
 * round-trip through the k8s API untouched.
 */

export type Environment = "dev" | "staging" | "prod";

export const ENVIRONMENTS: readonly Environment[] = ["dev", "staging", "prod"];

export const DEFAULT_ENVIRONMENT: Environment = "dev";

/** Real `metadata.labels` key set on every Project CR at provisioning time
 * (buildProjectManifest in lib/k8s.ts) -- same `platform-console.io/...`
 * label-prefix convention TIER_LABEL (lib/tiers.ts) and TAG_LABEL_PREFIX
 * (lib/tags.ts) already establish for "domain fact carried as a label". */
export const ENVIRONMENT_LABEL = "platform-console.io/environment";

const ENVIRONMENT_RANK: Record<Environment, number> = { dev: 0, staging: 1, prod: 2 };

export function isEnvironment(value: string): value is Environment {
  return value === "dev" || value === "staging" || value === "prod";
}

/**
 * The single next environment a Project promoted from `from` is allowed to
 * move to, or `null` when `from` is already the terminal environment
 * (`prod`). Promotion is deliberately restricted to exactly one forward
 * step at a time -- dev -> staging -> prod -- never a skip (dev straight to
 * prod) and never a reverse move (a "promotion" is, by definition, forward
 * only; demoting a Project back down an environment is not a capability
 * this module provides).
 */
export function nextEnvironment(from: Environment): Environment | null {
  if (from === "dev") return "staging";
  if (from === "staging") return "prod";
  return null;
}

/**
 * Real validation a guarded promote route runs before ever calling
 * requireApproval or patching the CR -- same "reject and 400, never a
 * partial/best-effort parse" discipline lib/freeze-windows.ts's
 * validateFreezeWindowInput already uses. Rejects skipping a stage
 * (dev -> prod), reversing (staging -> dev, prod -> staging), a no-op
 * (staging -> staging), and promoting past the terminal environment
 * (prod -> anything).
 */
export function validatePromotion(
  fromEnvironment: Environment,
  targetEnvironment: Environment,
): string | null {
  const expected = nextEnvironment(fromEnvironment);
  if (expected === null) {
    return `'${fromEnvironment}' is already the terminal environment -- there is nothing to promote it to`;
  }
  if (targetEnvironment !== expected) {
    return (
      `invalid promotion from '${fromEnvironment}' to '${targetEnvironment}' -- ` +
      `promotion only ever moves exactly one stage forward (dev -> staging -> prod); ` +
      `the only valid target from '${fromEnvironment}' is '${expected}'`
    );
  }
  return null;
}

/** Ordering helper mirroring lib/tiers.ts's tierAtLeast, kept in case a
 * future gate needs "is this Project at least staging" rather than an
 * exact-match check -- validatePromotion above never uses this (it always
 * requires the exact next stage), but callers reasoning about environment
 * order elsewhere in this console should use the same one ranking table
 * rather than re-deriving their own. */
export function environmentAtLeast(environment: Environment, minimum: Environment): boolean {
  return ENVIRONMENT_RANK[environment] >= ENVIRONMENT_RANK[minimum];
}
