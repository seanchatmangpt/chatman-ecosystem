/**
 * Custom RBAC roles / fine-grained permission grants -- the least-
 * privilege extension the fixed viewer/member/owner ladder in
 * lib/authz.ts cannot express (e.g. "billing-only admin", "read-only
 * auditor with DSAR export rights", "on-call engineer who can run castle
 * verbs but not change tiers"). This is strictly ADDITIVE on top of
 * lib/authz.ts's built-in role rank -- nothing about viewer/member/owner
 * changes, and a session with no custom role assignment behaves exactly
 * as it did before this module existed.
 *
 * Persisted the same way lib/authz.ts persists role-per-identifier: one
 * real k8s ConfigMap, reusing the exact get-then-create-or-patch
 * primitive lib/k8s.ts's Feature Flags module established
 * (getConfigMap / createOrUpdateConfigMap) -- no new k8s resource kind,
 * no new RBAC verb. Two kinds of `data` keys share this ConfigMap's
 * `data` map, disambiguated by prefix (same discipline lib/authz.ts uses
 * to keep bare role-assignment keys and `invite-<token>` keys in one
 * ConfigMap):
 *   - `role-<roleId>`   -> JSON-encoded CustomRole (the role definition)
 *   - `grant-<identifier>` -> JSON array of roleIds assigned to that
 *     identifier (encoded via authz.ts's encodeIdentifierKey so an email
 *     identifier is always a legal ConfigMap key byte sequence)
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";

export const CUSTOM_ROLES_NAMESPACE = "platform-console";
export const CUSTOM_ROLES_CONFIGMAP = "platform-console-custom-roles";

// The fine-grained permission registry. Deliberately a flat, closed list
// (not a free-form string) so every permission a custom role can grant is
// enumerable, greppable, and type-checked at every call site -- the same
// discipline lib/castle.ts's ALLOWED_CASTLE_VERBS applies to castle verbs.
export const PERMISSIONS = [
  "billing.manage",
  "castle.execute",
  "dsar.export",
  "tier.change",
  "apikeys.manage",
  "members.invite",
  "roles.manage",
  "audit.read",
  "secrets.manage",
  "backups.manage",
] as const;

export type Permission = (typeof PERMISSIONS)[number];

function isPermission(value: unknown): value is Permission {
  return typeof value === "string" && (PERMISSIONS as readonly string[]).includes(value);
}

export interface CustomRole {
  id: string;
  orgId: string;
  name: string;
  permissions: Permission[];
}

// Same escaping discipline as lib/authz.ts's encodeIdentifierKey: a k8s
// ConfigMap `data` key must match `[-._a-zA-Z0-9]+`, so any identifier
// byte outside that set (an email's `@`, `+`, etc.) is escaped as
// `-xHH-` (its hex code point) and decoded back on read.
function encodeKeyPart(part: string): string {
  return part.replace(/[^-._a-zA-Z0-9]/g, (ch) => `-x${ch.charCodeAt(0).toString(16)}-`);
}
function decodeKeyPart(part: string): string {
  return part.replace(/-x([0-9a-f]+)-/g, (_match, hex: string) =>
    String.fromCharCode(parseInt(hex, 16)),
  );
}

const ROLE_KEY_PREFIX = "role-";
const GRANT_KEY_PREFIX = "grant-";

function roleKey(roleId: string): string {
  return `${ROLE_KEY_PREFIX}${encodeKeyPart(roleId)}`;
}
function grantKey(identifier: string): string {
  return `${GRANT_KEY_PREFIX}${encodeKeyPart(identifier)}`;
}
function isRoleKey(key: string): boolean {
  return key.startsWith(ROLE_KEY_PREFIX);
}
function isGrantKey(key: string): boolean {
  return key.startsWith(GRANT_KEY_PREFIX);
}
function roleIdFromKey(key: string): string {
  return decodeKeyPart(key.slice(ROLE_KEY_PREFIX.length));
}
function identifierFromGrantKey(key: string): string {
  return decodeKeyPart(key.slice(GRANT_KEY_PREFIX.length));
}

function parseCustomRole(raw: string): CustomRole | null {
  try {
    const parsed = JSON.parse(raw) as Partial<CustomRole>;
    if (
      typeof parsed.id === "string" &&
      typeof parsed.orgId === "string" &&
      typeof parsed.name === "string" &&
      Array.isArray(parsed.permissions) &&
      parsed.permissions.every(isPermission)
    ) {
      return {
        id: parsed.id,
        orgId: parsed.orgId,
        name: parsed.name,
        permissions: parsed.permissions,
      };
    }
    return null;
  } catch {
    // A hand-edited or corrupt role record is skipped, not fatal -- same
    // "don't let one bad row break the whole list" discipline
    // lib/authz.ts's parseInvite applies.
    return null;
  }
}

function parseGrantList(raw: string): string[] {
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (Array.isArray(parsed) && parsed.every((v) => typeof v === "string")) {
      return parsed;
    }
    return [];
  } catch {
    return [];
  }
}

/**
 * Real read of every custom role definition in the platform's own
 * `platform-console-custom-roles` ConfigMap, scoped to one orgId. Same
 * `{ok:true, data:[]}`-on-not-provisioned convention as
 * lib/authz.ts's getOrgRoleAssignmentsIn.
 */
export async function listCustomRoles(orgId: string): Promise<K8sResult<CustomRole[]>> {
  const existing = await getConfigMap(CUSTOM_ROLES_NAMESPACE, CUSTOM_ROLES_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: [] };

  const roles: CustomRole[] = [];
  for (const [key, raw] of Object.entries(existing.data.data)) {
    if (!isRoleKey(key)) continue;
    const role = parseCustomRole(raw);
    if (role && role.orgId === orgId) roles.push(role);
  }
  return { ok: true, data: roles.sort((a, b) => a.name.localeCompare(b.name)) };
}

export async function getCustomRole(roleId: string): Promise<K8sResult<CustomRole | null>> {
  const existing = await getConfigMap(CUSTOM_ROLES_NAMESPACE, CUSTOM_ROLES_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: null };
  const raw = existing.data.data[roleKey(roleId)];
  if (!raw) return { ok: true, data: null };
  return { ok: true, data: parseCustomRole(raw) };
}

/**
 * Creates or updates a custom role definition via a real RFC 7386 merge
 * patch -- same one-key-at-a-time convention as lib/authz.ts's
 * setOrgRole. Caller is responsible for orgId scoping and for generating
 * a fresh id (crypto.randomUUID()) on create.
 */
export async function upsertCustomRole(role: CustomRole): Promise<K8sResult<CustomRole>> {
  const result = await createOrUpdateConfigMap(CUSTOM_ROLES_NAMESPACE, CUSTOM_ROLES_CONFIGMAP, {
    [roleKey(role.id)]: JSON.stringify(role),
  });
  if (!result.ok) return result;
  return { ok: true, data: role };
}

/**
 * Deletes a custom role definition. lib/k8s.ts exposes no "remove one
 * ConfigMap data key" primitive (createOrUpdateConfigMap only ever
 * adds/overwrites keys), so this is implemented as an empty-permissions,
 * empty-name tombstone rather than a true key removal -- the exact same
 * "revoke, don't delete" discipline lib/authz.ts's revokeOrgInviteIn
 * documents and applies to invite records, for the same reason (better
 * audit history, and no new k8s primitive required). listCustomRoles
 * filters tombstoned roles out via their empty `permissions` array.
 */
export async function deleteCustomRole(roleId: string): Promise<K8sResult<CustomRole | null>> {
  const existing = await getCustomRole(roleId);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: null };

  const tombstoned: CustomRole = { ...existing.data, name: `${existing.data.name} (deleted)`, permissions: [] };
  const result = await createOrUpdateConfigMap(CUSTOM_ROLES_NAMESPACE, CUSTOM_ROLES_CONFIGMAP, {
    [roleKey(roleId)]: JSON.stringify(tombstoned),
  });
  if (!result.ok) return result;
  return { ok: true, data: tombstoned };
}

/**
 * Real read of the roleIds assigned to one identifier (email for gotrue
 * users, "admin" for local-admin -- same identifier space
 * lib/authz.ts's roleIdentifierFor resolves).
 */
export async function getGrantsFor(identifier: string): Promise<K8sResult<string[]>> {
  const existing = await getConfigMap(CUSTOM_ROLES_NAMESPACE, CUSTOM_ROLES_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: [] };
  const raw = existing.data.data[grantKey(identifier)];
  if (!raw) return { ok: true, data: [] };
  return { ok: true, data: parseGrantList(raw) };
}

export interface CustomRoleGrant {
  identifier: string;
  roleIds: string[];
}

/**
 * Real read of every identifier -> roleId[] grant in this ConfigMap.
 * Used by the /app/org/roles admin UI to render "who has which custom
 * role" without one round trip per identifier.
 */
export async function listGrants(): Promise<K8sResult<CustomRoleGrant[]>> {
  const existing = await getConfigMap(CUSTOM_ROLES_NAMESPACE, CUSTOM_ROLES_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: [] };

  const grants: CustomRoleGrant[] = [];
  for (const [key, raw] of Object.entries(existing.data.data)) {
    if (!isGrantKey(key)) continue;
    const roleIds = parseGrantList(raw);
    if (roleIds.length > 0) {
      grants.push({ identifier: identifierFromGrantKey(key), roleIds });
    }
  }
  return { ok: true, data: grants.sort((a, b) => a.identifier.localeCompare(b.identifier)) };
}

/**
 * Sets the full set of custom-role assignments for one identifier (a
 * whole-array replace via one merge-patch key, mirroring how
 * lib/authz.ts's setOrgRole replaces one identifier's whole role value --
 * not an incremental add/remove primitive, so the caller sends the
 * complete desired roleId list each time).
 */
export async function setGrantsFor(
  identifier: string,
  roleIds: string[],
): Promise<K8sResult<CustomRoleGrant>> {
  const deduped = Array.from(new Set(roleIds));
  const result = await createOrUpdateConfigMap(CUSTOM_ROLES_NAMESPACE, CUSTOM_ROLES_CONFIGMAP, {
    [grantKey(identifier)]: JSON.stringify(deduped),
  });
  if (!result.ok) return result;
  return { ok: true, data: { identifier, roleIds: deduped } };
}

/**
 * hasPermission's real building block: does ANY custom role currently
 * assigned to this identifier, scoped to this orgId, grant the given
 * permission? Fails closed (false) on any k8s read error or missing
 * ConfigMap -- never throws, never silently grants.
 */
export async function identifierHasCustomPermission(
  identifier: string,
  orgId: string,
  permission: Permission,
): Promise<boolean> {
  const grantsResult = await getGrantsFor(identifier);
  if (!grantsResult.ok || grantsResult.data.length === 0) return false;

  const rolesResult = await listCustomRoles(orgId);
  if (!rolesResult.ok) return false;

  const grantedRoleIds = new Set(grantsResult.data);
  return rolesResult.data.some(
    (role) => grantedRoleIds.has(role.id) && role.permissions.includes(permission),
  );
}
