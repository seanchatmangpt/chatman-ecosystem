/**
 * Per-org onboarding checklist / setup-wizard completion tracker.
 *
 * Enterprise buyers piloting a new PaaS need a visible "time to first
 * value" artifact a CSM can show an exec sponsor mid-pilot -- and it has
 * to be trustworthy, i.e. computed from this org's REAL, live platform
 * state, never a self-reported checkbox a customer (or a CSM under
 * quota pressure) could tick without actually doing the work. Every step
 * below is a pure async `check(org)` that reads an EXISTING module this
 * console already has (lib/api-keys.ts, lib/k8s.ts, lib/authz.ts,
 * lib/custom-roles.ts) -- no new persisted "completion" state is
 * introduced anywhere, so the checklist can never drift from reality and
 * can never be faked by writing to a ConfigMap directly. Fail-closed:
 * any read error for a step is treated as "not done", never as "done" --
 * same discipline as lib/custom-roles.ts's identifierHasCustomPermission.
 */
import { listApiKeysForOrg } from "@/lib/api-keys";
import { getOrgRoleAssignmentsIn } from "@/lib/authz";
import { listCustomRoles, listGrants } from "@/lib/custom-roles";
import { listJobs, listProjects } from "@/lib/k8s";
import type { Org } from "@/lib/orgs";

export interface OnboardingStep {
  id: string;
  label: string;
  done: boolean;
}

export interface OnboardingResult {
  steps: OnboardingStep[];
  percentComplete: number;
}

interface StepDefinition {
  id: string;
  label: string;
  check(org: Org): Promise<boolean>;
}

/**
 * Fixed, ordered onboarding steps. Order matters for the rendered
 * checklist (earliest-value-first: auth, then a real workload, then
 * durability, then team/governance breadth) -- never re-sorted by
 * completion state, so a CSM sees the same walk-through every time.
 */
const STEPS: StepDefinition[] = [
  {
    id: "api-key-created",
    label: "Create an API key",
    async check(org) {
      const result = await listApiKeysForOrg(org.id);
      return result.ok && result.data.length > 0;
    },
  },
  {
    id: "first-project-ready",
    label: "Provision your first project and reach Ready",
    async check(org) {
      const result = await listProjects();
      if (!result.ok) return false;
      return result.data.some((p) => p.namespace === org.namespace && p.ready === true);
    },
  },
  {
    id: "first-backup-run",
    label: "Run your first database backup",
    async check(org) {
      const result = await listJobs(org.namespace);
      if (!result.ok) return false;
      return result.data.some((job) => job.status === "Complete");
    },
  },
  {
    id: "member-invited",
    label: "Invite an additional team member",
    async check(org) {
      const result = await getOrgRoleAssignmentsIn(org.namespace);
      if (!result.ok) return false;
      // A fresh org's own namespace-local roles ConfigMap is seeded with
      // exactly one entry -- the owner who created it (see lib/orgs.ts's
      // createOrg). More than one assignment means a real second member
      // has a real role in this org's namespace, not merely a pending,
      // unaccepted invite (an OrgInvite row alone grants no role and
      // therefore would not move this step -- deliberately: an invite
      // that was never accepted is not "team activated").
      return result.data.length > 1;
    },
  },
  {
    id: "custom-role-assigned",
    label: "Assign a custom role beyond the default owner",
    async check(org) {
      const rolesResult = await listCustomRoles(org.id);
      if (!rolesResult.ok || rolesResult.data.length === 0) return false;
      const liveRoleIds = new Set(
        rolesResult.data.filter((r) => r.permissions.length > 0).map((r) => r.id),
      );
      if (liveRoleIds.size === 0) return false;

      const grantsResult = await listGrants();
      if (!grantsResult.ok) return false;
      return grantsResult.data.some((grant) => grant.roleIds.some((id) => liveRoleIds.has(id)));
    },
  },
  {
    id: "sla-or-region-set",
    label: "Set an SLA tier or pin a data residency region",
    // Pure sync check over already-loaded org fields -- still exposed as
    // async to keep every StepDefinition's `check` the same shape/
    // Promise-returning signature, so `runOnboardingChecks` can `await`
    // all steps uniformly via Promise.all without a special case.
    async check(org) {
      return Boolean(org.slaTier || org.region);
    },
  },
];

/**
 * Runs every step's real check in parallel (each hits a different,
 * independent k8s/Secret/ConfigMap read -- no ordering dependency
 * between them) and computes the completion percentage from the results,
 * never from a separately-tracked counter.
 */
export async function runOnboardingChecks(org: Org): Promise<OnboardingResult> {
  const results = await Promise.all(
    STEPS.map(async (step) => ({
      id: step.id,
      label: step.label,
      done: await step.check(org).catch(() => false),
    })),
  );

  const percentComplete = Math.round(
    (results.filter((r) => r.done).length / results.length) * 100,
  );

  return { steps: results, percentComplete };
}
