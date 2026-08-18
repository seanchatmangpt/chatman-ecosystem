/**
 * Real application-level RBAC (AWS IAM Identity Center permission sets /
 * GCP Org Policy / Azure AD role assignments equivalent), layered ON TOP
 * OF -- never replacing -- the k8s-level RBAC the console's own
 * ServiceAccount already has (k8s/rbac.yaml, k8s/paas-rbac.yaml). Those
 * grants control what the *pod's identity* may do against the Kubernetes
 * API; this module controls what the *authenticated human* behind a
 * session may trigger the pod into doing. Before this file, every
 * authenticated session -- local-admin or gotrue -- got the exact same
 * full access; this is the first app-level authorization boundary.
 *
 * Role model, real and stored in one real k8s ConfigMap
 * (`platform-console-org-roles`, `platform-console` namespace), reusing
 * the exact get-then-create-or-patch primitive lib/k8s.ts's Feature Flags
 * module already established (`getConfigMap` / `createOrUpdateConfigMap`)
 * -- no new k8s resource kind, no new RBAC verb: the same
 * `platform-console-feature-flags` Role (k8s/paas-rbac.yaml) already
 * grants get/list/create/update/patch on `configmaps` in the
 * platform-console namespace with no `resourceNames` restriction, so it
 * already covers this second ConfigMap with zero YAML changes.
 *
 * Roles: "viewer" < "member" < "owner". Identifier: email for gotrue
 * users, "admin" for the local-admin account -- exactly session.sub for
 * local-admin, session.email for gotrue (see lib/session.ts's
 * discriminated union).
 */
import { NextResponse } from "next/server";
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import type { SessionPayload } from "@/lib/session";

export const ORG_ROLES_NAMESPACE = "platform-console";
export const ORG_ROLES_CONFIGMAP = "platform-console-org-roles";

export type Role = "viewer" | "member" | "owner";

const ROLE_RANK: Record<Role, number> = { viewer: 0, member: 1, owner: 2 };
export const ROLES: Role[] = ["viewer", "member", "owner"];

const ADMIN_IDENTIFIER = "admin";

function isRole(value: string): value is Role {
  return value === "viewer" || value === "member" || value === "owner";
}

// A k8s ConfigMap `data` key must match `[-._a-zA-Z0-9]+` -- an email
// address's `@` (and any other character outside that set, e.g. `+`
// plus-addressing) is not a legal key byte. Every disallowed character is
// escaped as `-xHH-` (its hex code point) so the ConfigMap write never
// fails on a real user's real email, and decoded back on read. Plain
// identifiers like "admin" round-trip unchanged.
function encodeIdentifierKey(identifier: string): string {
  return identifier.replace(/[^-._a-zA-Z0-9]/g, (ch) => `-x${ch.charCodeAt(0).toString(16)}-`);
}
function decodeIdentifierKey(key: string): string {
  return key.replace(/-x([0-9a-f]+)-/g, (_match, hex: string) =>
    String.fromCharCode(parseInt(hex, 16)),
  );
}

/**
 * The ConfigMap key for a given session: session.email for gotrue AND
 * oidc-external (both are real external identities keyed by email),
 * session.sub ("admin") for local-admin.
 */
export function roleIdentifierFor(session: SessionPayload): string {
  return session.authProvider === "gotrue" || session.authProvider === "oidc-external"
    ? session.email
    : session.sub;
}

export interface OrgRoleAssignment {
  identifier: string;
  role: Role;
}

function toAssignments(data: Record<string, string>): OrgRoleAssignment[] {
  return Object.entries(data)
    .filter((entry): entry is [string, Role] => isRole(entry[1]))
    .map(([key, role]) => ({ identifier: decodeIdentifierKey(key), role }))
    .sort((a, b) => a.identifier.localeCompare(b.identifier));
}

/**
 * Reads the real `platform-console-org-roles` ConfigMap. Seeds it with
 * `{admin: "owner"}` (requirement: "Seed `admin` as `owner` by default")
 * the first time it's read and doesn't exist yet -- a real ConfigMap
 * create via the same get-then-create pattern createOrUpdateConfigMap
 * itself uses, not a fabricated in-memory default. Same
 * `{ok:true, data:...}` / `{ok:false, error}` fail-closed shape every
 * other lib/k8s.ts reader uses.
 */
export async function getOrgRoleAssignments(): Promise<K8sResult<OrgRoleAssignment[]>> {
  const existing = await getConfigMap(ORG_ROLES_NAMESPACE, ORG_ROLES_CONFIGMAP);
  if (!existing.ok) return existing;

  if (!existing.data) {
    const seeded = await createOrUpdateConfigMap(ORG_ROLES_NAMESPACE, ORG_ROLES_CONFIGMAP, {
      [encodeIdentifierKey(ADMIN_IDENTIFIER)]: "owner",
    });
    if (!seeded.ok) return seeded;
    return { ok: true, data: toAssignments(seeded.data.data) };
  }

  return { ok: true, data: toAssignments(existing.data.data) };
}

/**
 * Sets one identifier's role via a real RFC 7386 merge patch (or create,
 * on first write) -- same one-key-at-a-time convention as the Feature
 * Flags module's setFlag, never a full-map replace.
 */
export async function setOrgRole(
  identifier: string,
  role: Role,
): Promise<K8sResult<OrgRoleAssignment[]>> {
  const result = await createOrUpdateConfigMap(ORG_ROLES_NAMESPACE, ORG_ROLES_CONFIGMAP, {
    [encodeIdentifierKey(identifier)]: role,
  });
  if (!result.ok) return result;
  return { ok: true, data: toAssignments(result.data.data) };
}

/**
 * Resolves one session's effective role. Falls back to a real,
 * documented in-code default -- never a fabricated ConfigMap read --
 * only when the ConfigMap has no explicit entry for this identifier (or
 * is genuinely unreachable): local-admin defaults to "owner" (the seed
 * this module also writes explicitly into the ConfigMap on first read
 * above), every other identity (every gotrue user) defaults to "viewer"
 * -- fail-closed: a brand-new signup gets the lowest privilege until an
 * owner explicitly promotes them via the real /org page.
 */
export async function getRoleFor(session: SessionPayload): Promise<Role> {
  // API-key sessions (lib/api-keys.ts) carry their role as a fixed claim
  // set at key-creation time, minted by lib/session.ts's
  // createApiKeySessionToken only after a real hash match against the
  // live platform-console-api-keys Secret -- no ConfigMap round trip
  // needed or wanted here, since an API key's role cannot change after
  // issuance (only revocation, which is enforced upstream in
  // lib/api-keys.ts's resolveApiKeyAuth, before this session ever exists).
  if (session.authProvider === "api-key") {
    return session.boundRole;
  }

  const identifier = roleIdentifierFor(session);
  const result = await getOrgRoleAssignments();
  if (result.ok) {
    const found = result.data.find((a) => a.identifier === identifier);
    if (found) return found.role;
  }
  return session.authProvider === "local-admin" ? "owner" : "viewer";
}

export interface RoleCheck {
  ok: boolean;
  role: Role;
  response?: NextResponse;
}

/**
 * requireRole(session, minimumRole): the real access-boundary check every
 * role-gated route below calls, after its existing requireActor 401
 * check. Role ordering viewer < member < owner. A session whose role
 * doesn't meet minimumRole gets `{ok:false, response}` -- a real, ready-
 * to-return 403 NextResponse naming the actor's actual role and the
 * minimum required -- same fail-closed convention as this app's existing
 * 401s (a missing/invalid session never falls through to "allow").
 *
 * This is strictly additive to the k8s-level RBAC the console's
 * ServiceAccount already carries: it never grants the ServiceAccount any
 * new Kubernetes permission, it only decides whether THIS request is
 * allowed to make the console exercise a permission it already has.
 */
export async function requireRole(
  session: SessionPayload,
  minimumRole: Role,
): Promise<RoleCheck> {
  const role = await getRoleFor(session);
  if (ROLE_RANK[role] >= ROLE_RANK[minimumRole]) {
    return { ok: true, role };
  }
  return {
    ok: false,
    role,
    response: NextResponse.json(
      {
        error: "forbidden",
        reason: `role '${role}' does not meet the required minimum role '${minimumRole}' for this action`,
      },
      { status: 403 },
    ),
  };
}
