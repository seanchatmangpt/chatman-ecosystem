/**
 * Real SSO/SCIM role-mapping drift computation -- the report a Fortune-5
 * enterprise security review board asks for by name before granting an
 * app SSO trust: "compare your configured group-to-role mapping against
 * who actually holds which role today, and show us the gap."
 *
 * Honest scope boundary, stated plainly up front rather than buried:
 * this app has no live SCIM/IdP group-membership feed today (grep for
 * "scim"/"groups" across lib/session.ts and lib/oidc-federation.ts turns
 * up nothing -- neither the gotrue nor the oidc-external session variant
 * carries a group claim). This module therefore does NOT attempt to
 * compute "does user X's real IdP group entitle them to role Y" --
 * that would require fabricating a per-user group-membership record this
 * app does not actually have, which this codebase's own conventions
 * (lib/k8s-fault-scan.ts's "diagnose only from real, observed state"
 * discipline) forbid.
 *
 * What it computes instead is real and useful on its own: it diffs the
 * ORG'S OWN DECLARED INTENT (lib/sso-role-mapping.ts's configured
 * `SsoGroupRoleMapping[]`, an owner-authored, approval-gated record) --
 * i.e., the SET of roles the org has told this platform its SSO groups
 * are supposed to be able to grant -- against the real, live,
 * ConfigMap-backed `OrgRoleAssignment[]` (lib/authz.ts's
 * getOrgRoleAssignmentsIn, the actual assigned role for every real
 * identifier in this org's own namespace). Two real drift classes fall
 * out of that diff, both computed only from real, already-persisted
 * state, no fabricated group membership involved:
 *
 *   - `unmapped_role_in_use` ("orphaned/over-privileged candidate"): a
 *     real identifier holds a role for which the org's OWN configured
 *     mapping set declares NO SSO group grants that role at all. Under
 *     the org's stated SSO policy, nobody should hold this role via SSO
 *     -- so an identifier holding it anyway is either a pre-SSO local
 *     grant that was never cleaned up, or a role assigned outside the
 *     declared SSO governance model. Exactly the "orphaned/
 *     over-privileged account" class the pitch names.
 *   - `unused_mapping` (stale declared intent): a configured mapping
 *     declares an SSO group grants some role, but NO real identifier in
 *     this org currently holds that role -- the declared mapping has
 *     drifted from reality in the other direction (a group that was
 *     supposed to be in use isn't backing anyone today), worth a review
 *     board flagging as much as the first class.
 *
 * Pure function over already-fetched real data -- no k8s I/O of its own,
 * same "computation is pure, the route/caller does the real reads"
 * split lib/k8s-fault-scan-history.ts's buildFaultScanSnapshot uses.
 */
import type { Role } from "@/lib/authz";
import type { OrgRoleAssignment } from "@/lib/authz";
import type { SsoGroupRoleMapping } from "@/lib/sso-role-mapping";

export type SsoRoleDriftFindingKind = "unmapped_role_in_use" | "unused_mapping";

export interface SsoRoleDriftFinding {
  kind: SsoRoleDriftFindingKind;
  role: Role;
  /** Real assigned identifier holding `role` with no backing SSO group
   * mapping -- present only for `unmapped_role_in_use`. */
  identifier?: string;
  /** Configured SSO group that maps to `role` but currently backs no
   * real assignment -- present only for `unused_mapping`. */
  ssoGroup?: string;
}

export interface SsoRoleDriftReport {
  orgId: string;
  generatedAt: string;
  configuredMappings: SsoGroupRoleMapping[];
  actualAssignmentCount: number;
  findings: SsoRoleDriftFinding[];
  /** Count of real identifiers holding a role no configured SSO group
   * maps to -- the headline "over-privileged/orphaned account" number a
   * review board reads first. */
  unmappedRoleInUseCount: number;
  /** Count of configured mappings that currently back zero real
   * assignments. */
  unusedMappingCount: number;
}

/**
 * Real diff, computed only from the two real inputs -- never fabricated
 * per-user group membership (see this module's own doc comment above
 * for why that boundary is drawn where it is).
 */
export function computeSsoRoleDrift(
  orgId: string,
  configuredMappings: SsoGroupRoleMapping[],
  actualAssignments: OrgRoleAssignment[],
  generatedAt: string = new Date().toISOString(),
): SsoRoleDriftReport {
  const mappedRoles = new Set<Role>(configuredMappings.map((m) => m.role));
  const assignedRoles = new Set<Role>(actualAssignments.map((a) => a.role));

  const findings: SsoRoleDriftFinding[] = [];

  for (const assignment of actualAssignments) {
    if (!mappedRoles.has(assignment.role)) {
      findings.push({
        kind: "unmapped_role_in_use",
        role: assignment.role,
        identifier: assignment.identifier,
      });
    }
  }

  for (const mapping of configuredMappings) {
    if (!assignedRoles.has(mapping.role)) {
      findings.push({
        kind: "unused_mapping",
        role: mapping.role,
        ssoGroup: mapping.ssoGroup,
      });
    }
  }

  const unmappedRoleInUseCount = findings.filter((f) => f.kind === "unmapped_role_in_use").length;
  const unusedMappingCount = findings.filter((f) => f.kind === "unused_mapping").length;

  return {
    orgId,
    generatedAt,
    configuredMappings,
    actualAssignmentCount: actualAssignments.length,
    findings,
    unmappedRoleInUseCount,
    unusedMappingCount,
  };
}
