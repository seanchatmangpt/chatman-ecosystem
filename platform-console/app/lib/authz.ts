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

// Matches every org-scoped route this app has (`/orgs/<id>/...` pages and
// `/api/orgs/<id>/...` routes) -- both share the same `<id>` segment
// shape, the org id lib/orgs.ts's getOrg/createOrg use and the exact
// value lib/impersonation.ts's targetOrgId is stored as (see
// app/api/support/impersonate/route.ts's POST, which passes the same
// `targetOrgId` straight to both `getOrg` and `startImpersonation`).
// Deliberately a plain path match, not a live `getOrg` lookup: this is
// used by middleware.ts on every request to decide whether an active
// impersonation session's targetOrgId applies to the org THIS request is
// scoped to, and middleware must stay a lightweight, synchronous-shaped
// check -- not a second k8s round trip on top of the one the route
// handler itself will already make.
const ORG_SCOPED_PATH_PATTERN = /^\/(?:api\/)?orgs\/([^/]+)(?:\/|$)/;

/**
 * Extracts the org id a request path is scoped to, if any -- `null` for
 * every path that isn't under `/orgs/<id>` or `/api/orgs/<id>`. The
 * captured segment is URL-decoded so an org id containing characters that
 * needed percent-encoding in the URL still compares equal to the plain
 * id lib/orgs.ts and lib/impersonation.ts operate on.
 */
export function orgIdFromRequestPath(pathname: string): string | null {
  const match = ORG_SCOPED_PATH_PATTERN.exec(pathname);
  if (!match) return null;
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return match[1];
  }
}

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

/**
 * Namespace-scoped variant of getRoleFor, for the customer-org
 * ConfigMaps createOrg (lib/orgs.ts) seeds inside EACH org's own
 * namespace -- not the platform's own `platform-console` namespace
 * getRoleFor/getOrgRoleAssignments always read. Same ConfigMap name
 * (`ORG_ROLES_CONFIGMAP`), same encode/decode and default-role rules,
 * just parameterized by namespace so a call against org A's namespace
 * can never see or be satisfied by org B's (or the platform's own)
 * role assignments.
 */
export async function getOrgRoleAssignmentsIn(
  namespace: string,
): Promise<K8sResult<OrgRoleAssignment[]>> {
  const existing = await getConfigMap(namespace, ORG_ROLES_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: [] };
  return { ok: true, data: toAssignments(existing.data.data) };
}

/**
 * Namespace-scoped counterpart to setOrgRole, for the same
 * `platform-console-org-roles` ConfigMap seeded per customer org
 * (lib/orgs.ts's createOrg). Used by acceptOrgInviteIn below to promote
 * an accepted invite into a real role entry inside THAT org's own
 * namespace -- never the platform's own `platform-console` namespace
 * setOrgRole writes to.
 */
export async function setOrgRoleIn(
  namespace: string,
  identifier: string,
  role: Role,
): Promise<K8sResult<OrgRoleAssignment[]>> {
  const result = await createOrUpdateConfigMap(namespace, ORG_ROLES_CONFIGMAP, {
    [encodeIdentifierKey(identifier)]: role,
  });
  if (!result.ok) return result;
  return { ok: true, data: toAssignments(result.data.data) };
}

export async function getRoleForIn(session: SessionPayload, namespace: string): Promise<Role> {
  if (session.authProvider === "api-key") {
    return session.boundRole;
  }

  const identifier = roleIdentifierFor(session);
  const result = await getOrgRoleAssignmentsIn(namespace);
  if (result.ok) {
    const found = result.data.find((a) => a.identifier === identifier);
    if (found) return found.role;
  }
  return "viewer";
}

/**
 * requireRole's namespace-scoped counterpart -- same fail-closed 403
 * shape, checked against one specific customer org's own namespace-local
 * `platform-console-org-roles` ConfigMap instead of the platform's own.
 * Used by app/api/orgs/[id]/branding/route.ts's PUT, which must gate on
 * "owner of THIS org", not "owner of the platform console".
 */
export async function requireRoleIn(
  session: SessionPayload,
  namespace: string,
  minimumRole: Role,
): Promise<RoleCheck> {
  const role = await getRoleForIn(session, namespace);
  if (ROLE_RANK[role] >= ROLE_RANK[minimumRole]) {
    return { ok: true, role };
  }
  return {
    ok: false,
    role,
    response: NextResponse.json(
      {
        error: "forbidden",
        reason: `role '${role}' does not meet the required minimum role '${minimumRole}' for this org`,
      },
      { status: 403 },
    ),
  };
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

// ---------------------------------------------------------------------
// Seat-based invites: per-org pending/accepted invite records, reusing
// the exact same `platform-console-org-roles` ConfigMap and
// get-then-create-or-patch primitive as the role assignments above --
// no new k8s kind. A role assignment entry's `data` value is a bare
// Role string ("viewer"/"member"/"owner"); an invite entry's value is a
// JSON-encoded OrgInvite. Both live in the same ConfigMap `data` map,
// disambiguated by key prefix (`invite-<token>` vs. a bare identifier
// key) and by toAssignments' own isRole filter (a JSON invite value is
// never a valid Role string, so it's already excluded from
// getOrgRoleAssignmentsIn's results without any extra filtering there).
// ---------------------------------------------------------------------

export type InviteStatus = "pending" | "accepted" | "revoked";

export interface OrgInvite {
  token: string;
  email: string;
  role: Role;
  invitedBy: string;
  invitedAt: string;
  expiresAt: string;
  status: InviteStatus;
}

const INVITE_KEY_PREFIX = "invite-";
const INVITE_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days, same as most SaaS invite links

function inviteKey(token: string): string {
  return `${INVITE_KEY_PREFIX}${token}`;
}

function isInviteKey(key: string): boolean {
  return key.startsWith(INVITE_KEY_PREFIX);
}

function isInviteStatus(value: unknown): value is InviteStatus {
  return value === "pending" || value === "accepted" || value === "revoked";
}

function parseInvite(raw: string): OrgInvite | null {
  try {
    const parsed = JSON.parse(raw) as Partial<OrgInvite>;
    if (
      typeof parsed.token === "string" &&
      typeof parsed.email === "string" &&
      typeof parsed.role === "string" &&
      isRole(parsed.role) &&
      typeof parsed.invitedBy === "string" &&
      typeof parsed.invitedAt === "string" &&
      typeof parsed.expiresAt === "string" &&
      isInviteStatus(parsed.status)
    ) {
      return parsed as OrgInvite;
    }
    return null;
  } catch {
    // A hand-edited or corrupt invite record is skipped, not fatal --
    // same "don't let one bad row break the whole list" discipline
    // toAssignments already applies to role entries.
    return null;
  }
}

/**
 * Real read of every invite record (pending, accepted, and revoked) in
 * one org's own namespace-local `platform-console-org-roles` ConfigMap.
 * Same `{ok:true, data:[]}`-on-not-provisioned convention as
 * getOrgRoleAssignmentsIn.
 */
export async function listOrgInvitesIn(namespace: string): Promise<K8sResult<OrgInvite[]>> {
  const existing = await getConfigMap(namespace, ORG_ROLES_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: [] };

  const invites: OrgInvite[] = [];
  for (const [key, raw] of Object.entries(existing.data.data)) {
    if (!isInviteKey(key)) continue;
    const invite = parseInvite(raw);
    if (invite) invites.push(invite);
  }
  return { ok: true, data: invites.sort((a, b) => b.invitedAt.localeCompare(a.invitedAt)) };
}

export async function getOrgInviteIn(
  namespace: string,
  token: string,
): Promise<K8sResult<OrgInvite | null>> {
  const existing = await getConfigMap(namespace, ORG_ROLES_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: null };
  const raw = existing.data.data[inviteKey(token)];
  if (!raw) return { ok: true, data: null };
  return { ok: true, data: parseInvite(raw) };
}

/**
 * Real seat count for one org: accepted role assignments PLUS still-open
 * (non-expired) pending invites. Both a real member and a real
 * outstanding invite occupy a seat -- an owner who sends 25 invites on a
 * 25-seat Pro plan and none of them have been accepted yet has still
 * used every seat, exactly like Vercel/Retool/Auth0 count a pending seat
 * against the quota so a customer can't oversell invites past their
 * subscription.
 */
export async function countUsedSeatsIn(
  namespace: string,
): Promise<K8sResult<{ accepted: number; pending: number; used: number }>> {
  const [rolesResult, invitesResult] = await Promise.all([
    getOrgRoleAssignmentsIn(namespace),
    listOrgInvitesIn(namespace),
  ]);
  if (!rolesResult.ok) return rolesResult;
  if (!invitesResult.ok) return invitesResult;

  const now = Date.now();
  const accepted = rolesResult.data.length;
  const pending = invitesResult.data.filter(
    (invite) => invite.status === "pending" && new Date(invite.expiresAt).getTime() > now,
  ).length;
  return { ok: true, data: { accepted, pending, used: accepted + pending } };
}

/**
 * Creates a real pending invite -- caller (the API route) is responsible
 * for the seat-limit 403 check against SEAT_LIMITS BEFORE calling this,
 * since that check needs the org's ProjectTier (lib/tiers.ts), which
 * this module has no dependency on. A fresh, unguessable token is minted
 * via crypto.randomUUID() (already used the same way by lib/orgs.ts's
 * org-id and namespace-suffix generation) -- its charset ([0-9a-f-]) is
 * already a legal k8s ConfigMap key byte, so no escaping is needed here,
 * unlike encodeIdentifierKey for arbitrary email identifiers.
 */
export async function createOrgInviteIn(
  namespace: string,
  input: { email: string; role: Role; invitedBy: string },
): Promise<K8sResult<OrgInvite>> {
  const now = new Date();
  const invite: OrgInvite = {
    token: globalThis.crypto.randomUUID(),
    email: input.email,
    role: input.role,
    invitedBy: input.invitedBy,
    invitedAt: now.toISOString(),
    expiresAt: new Date(now.getTime() + INVITE_TTL_MS).toISOString(),
    status: "pending",
  };
  const result = await createOrUpdateConfigMap(namespace, ORG_ROLES_CONFIGMAP, {
    [inviteKey(invite.token)]: JSON.stringify(invite),
  });
  if (!result.ok) return result;
  return { ok: true, data: invite };
}

/**
 * Promotes a pending invite into a real role entry (via setOrgRoleIn)
 * and marks the invite record `status: "accepted"` -- two writes to the
 * same ConfigMap, same merge-patch-per-key discipline as every other
 * mutation in this file. Fails closed: an already-accepted/revoked
 * invite, an expired invite, or an accepting identity that doesn't match
 * the invited email is rejected with a real, specific error string
 * rather than silently promoting the wrong identity or double-granting a
 * role.
 */
export async function acceptOrgInviteIn(
  namespace: string,
  token: string,
  acceptingIdentifier: string,
): Promise<K8sResult<OrgInvite>> {
  const existing = await getOrgInviteIn(namespace, token);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: false, error: "invite not found" };
  if (existing.data.status !== "pending") {
    return { ok: false, error: `invite is already ${existing.data.status}` };
  }
  if (new Date(existing.data.expiresAt).getTime() <= Date.now()) {
    return { ok: false, error: "invite has expired" };
  }
  if (existing.data.email.toLowerCase() !== acceptingIdentifier.toLowerCase()) {
    return { ok: false, error: "invite email does not match the authenticated identity" };
  }

  const roleResult = await setOrgRoleIn(namespace, acceptingIdentifier, existing.data.role);
  if (!roleResult.ok) return roleResult;

  const accepted: OrgInvite = { ...existing.data, status: "accepted" };
  const result = await createOrUpdateConfigMap(namespace, ORG_ROLES_CONFIGMAP, {
    [inviteKey(token)]: JSON.stringify(accepted),
  });
  if (!result.ok) return result;
  return { ok: true, data: accepted };
}

/**
 * Revokes a pending invite -- implemented as a merge-patch of that
 * invite's own JSON value to `status: "revoked"`, not a k8s key
 * deletion: lib/k8s.ts exposes no "remove one ConfigMap data key"
 * primitive (createOrUpdateConfigMap only ever adds/overwrites keys), so
 * revocation reuses that exact same primitive rather than introducing a
 * new one -- and a revoked-not-deleted record is arguably better audit
 * history anyway (an owner can see WHO revoked WHAT, not just that a
 * token silently vanished).
 */
export async function revokeOrgInviteIn(
  namespace: string,
  token: string,
): Promise<K8sResult<OrgInvite>> {
  const existing = await getOrgInviteIn(namespace, token);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: false, error: "invite not found" };
  if (existing.data.status !== "pending") {
    return { ok: false, error: `invite is already ${existing.data.status}` };
  }

  const revoked: OrgInvite = { ...existing.data, status: "revoked" };
  const result = await createOrUpdateConfigMap(namespace, ORG_ROLES_CONFIGMAP, {
    [inviteKey(token)]: JSON.stringify(revoked),
  });
  if (!result.ok) return result;
  return { ok: true, data: revoked };
}

// ---------------------------------------------------------------------
// Platform-admin gate: the "platform-admin role" the Admin Impersonation
// spec (lib/impersonation.ts, /api/support/impersonate) requires. This
// codebase's role model has exactly one PLATFORM-wide (as opposed to
// per-customer-org) role assignment set: the `platform-console-org-roles`
// ConfigMap in the `platform-console` namespace that getOrgRoleAssignments
// / requireRole already read -- "owner" there is, and always has been,
// the platform operator's own admin role (the local-admin account is
// seeded into it as "owner" by default, see getOrgRoleAssignments' doc
// comment above). "platform-admin" is therefore not a fourth Role rank to
// add to ROLE_RANK (which would fork every existing per-org owner/member/
// viewer comparison); it's this exact existing check -- an "owner" of the
// platform's own roles ConfigMap -- named and exposed under the identifier
// the spec uses, so a support-impersonation route can gate on it without
// silently reinventing what "owner" already means at the platform level.
export interface PlatformAdminCheck {
  ok: boolean;
  response?: NextResponse;
}

export async function requirePlatformAdmin(session: SessionPayload): Promise<PlatformAdminCheck> {
  const access = await requireRole(session, "owner");
  if (access.ok) return { ok: true };
  return {
    ok: false,
    response: NextResponse.json(
      {
        error: "forbidden",
        reason: `role '${access.role}' does not have platform-admin (platform-level owner) access required to start a support-impersonation session`,
      },
      { status: 403 },
    ),
  };
}
