/**
 * Real, config-only SSO group -> app role mapping surface -- the piece
 * enterprise security review boards ask for BEFORE granting SSO trust to
 * a vendor console: "show us exactly which of your IdP groups map to
 * which of your app's privilege levels, and prove your currently
 * assigned roles actually match that mapping." lib/saml-config.ts closes
 * "can this org configure its IdP metadata"; this module closes the
 * separate, later question "given that IdP, which of its groups grants
 * which role here" -- config-only, same fail-closed posture as
 * lib/saml-config.ts: no code path here provisions or deprovisions a
 * role automatically from a real IdP group claim (this app has no live
 * SCIM/group-claim ingestion today -- see lib/sso-role-drift.ts's module
 * doc for the honest, disclosed scope boundary that follows from that).
 * This module only lets an org owner declare the INTENDED mapping and
 * validates it structurally, the same "declare + validate offline, wire
 * the real enforcement later" split lib/saml-config.ts already
 * establishes for SAML metadata itself.
 *
 * Persisted via lib/orgs.ts's `ssoGroupMappings` field on the org
 * registry entry, same one-key-at-a-time merge-patch discipline
 * `samlConfig` already uses on that same ConfigMap -- no new k8s
 * resource kind, no new RBAC verb.
 */
import type { Role } from "@/lib/authz";
import { ROLES } from "@/lib/authz";

export interface SsoGroupRoleMapping {
  /** The IdP-side group name/claim value (e.g. "okta-platform-owners",
   * "AzureAD-Engineering-SRE") an org admin asserts should confer `role`
   * to any member of it. Free text: this app does not validate it
   * against a live IdP directory (no network call, same offline-only
   * posture lib/saml-config.ts's validateSamlConfig already documents
   * for the SAML metadata triple), only that it is non-empty and unique
   * within this org's mapping set. */
  ssoGroup: string;
  role: Role;
}

const MAX_GROUP_NAME_LENGTH = 256;
const MAX_MAPPINGS = 100;

function isRole(value: unknown): value is Role {
  return typeof value === "string" && (ROLES as readonly string[]).includes(value);
}

export function isSsoGroupRoleMapping(value: unknown): value is SsoGroupRoleMapping {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return typeof v.ssoGroup === "string" && v.ssoGroup.length > 0 && isRole(v.role);
}

/**
 * Structural, offline validation of a submitted mapping set -- same
 * "reject and return a real, specific error string, never a fabricated
 * silent default/pass" discipline as lib/saml-config.ts's
 * validateSamlConfig. Rejects an empty group name, a group name over the
 * length ceiling, a non-`Role` role value, a duplicate group name within
 * the same submitted set, and a submission over `MAX_MAPPINGS` entries
 * (bounds the ConfigMap value well under k8s's 1MiB ceiling, same
 * reasoning lib/k8s-fault-scan-history.ts's MAX_SNAPSHOTS_PER_KEY
 * documents for its own cap). Returns `null` on success, matching every
 * other validator in this codebase.
 */
export function validateSsoGroupMappings(mappings: unknown): string | null {
  if (!Array.isArray(mappings)) {
    return "mappings must be an array";
  }
  if (mappings.length > MAX_MAPPINGS) {
    return `mappings must contain at most ${MAX_MAPPINGS} entries`;
  }
  const seen = new Set<string>();
  for (const raw of mappings) {
    if (!raw || typeof raw !== "object") {
      return "each mapping must be an object with ssoGroup and role";
    }
    const entry = raw as Record<string, unknown>;
    const ssoGroup = typeof entry.ssoGroup === "string" ? entry.ssoGroup.trim() : "";
    if (!ssoGroup || ssoGroup.length > MAX_GROUP_NAME_LENGTH) {
      return `ssoGroup is required and must be at most ${MAX_GROUP_NAME_LENGTH} characters`;
    }
    if (!isRole(entry.role)) {
      return `role must be one of: ${ROLES.join(", ")}`;
    }
    if (seen.has(ssoGroup)) {
      return `duplicate ssoGroup in mapping set: '${ssoGroup}'`;
    }
    seen.add(ssoGroup);
  }
  return null;
}

/**
 * Normalizes an already-validated submission into the real
 * `SsoGroupRoleMapping[]` shape persisted by lib/orgs.ts's
 * setOrgSsoGroupMappings -- callers must run `validateSsoGroupMappings`
 * first, same "route/lib-caller validates, this trims and shapes
 * already-valid input" split lib/saml-config.ts's own callers use.
 */
export function normalizeSsoGroupMappings(mappings: unknown[]): SsoGroupRoleMapping[] {
  return mappings.map((raw) => {
    const entry = raw as Record<string, unknown>;
    return {
      ssoGroup: (entry.ssoGroup as string).trim(),
      role: entry.role as Role,
    };
  });
}
