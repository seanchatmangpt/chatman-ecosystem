import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import {
  deleteCustomRole,
  getCustomRole,
  listCustomRoles,
  listGrants,
  PERMISSIONS,
  setGrantsFor,
  upsertCustomRole,
  type CustomRole,
  type Permission,
} from "@/lib/custom-roles";

// Backs the owner-only /org/roles page (app/org/roles/page.tsx). Custom
// RBAC role definitions and grants are org-scoped, but defining/assigning
// them is itself owner-gated -- same enforcement boundary discipline as
// /api/org/roles: real server-side requireRole(session, "owner"), not
// just hidden client-side. Runs on the Node.js runtime (default for route
// handlers), same as every other /api/* route calling into lib/k8s.ts.

const DEFAULT_ORG_ID = "platform-console";

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isPermissionArray(value: unknown): value is Permission[] {
  return Array.isArray(value) && value.every((v) => (PERMISSIONS as readonly string[]).includes(v));
}

/**
 * GET: lists every custom role definition and every identifier -> roleId
 * grant, both scoped to `?orgId=` (defaults to the platform's own
 * "platform-console" scope, matching the un-namespaced orgId lib/authz.ts's
 * getOrgRoleAssignments already operates against).
 */
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      // org-agnostic: this 403 branch fires before ?orgId= is parsed below
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/roles",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim() || DEFAULT_ORG_ID;

  const [rolesResult, grantsResult] = await Promise.all([listCustomRoles(orgId), listGrants()]);

  const ok = rolesResult.ok && grantsResult.ok;
  writeAuditLogEntry({
    orgId: orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/roles",
    status: ok ? 200 : 502,
    requestId,
  });

  if (!rolesResult.ok) return NextResponse.json({ error: rolesResult.error }, { status: 502 });
  if (!grantsResult.ok) return NextResponse.json({ error: grantsResult.error }, { status: 502 });

  return NextResponse.json({
    permissions: PERMISSIONS,
    roles: rolesResult.data,
    grants: grantsResult.data,
  });
}

type RolesPostBody =
  | {
      action: "upsert-role";
      id?: string;
      orgId?: string;
      orgIds?: unknown;
      name: string;
      permissions: unknown;
    }
  | { action: "delete-role"; id: string }
  | { action: "set-grants"; identifier: string; roleIds: unknown };

/**
 * POST: three real, owner-gated mutations against the
 * `platform-console-custom-roles` ConfigMap, dispatched by `action` --
 * mirrors /api/org/roles's single-purpose POST but a custom role needs
 * create/update/delete/assign, not just "set one value", so this route
 * takes an explicit discriminator instead of overloading a bare
 * identifier+role POST body the way /api/org/roles does.
 */
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      // org-agnostic: this action can target multiple orgIds (see orgIds below) and the body hasn't been parsed yet at this point anyway
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/roles",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = (await request.json().catch(() => null)) as Partial<RolesPostBody> | null;
  if (!body || typeof body.action !== "string") {
    return NextResponse.json(
      { error: "action is required and must be one of: upsert-role, delete-role, set-grants" },
      { status: 400 },
    );
  }

  let result: { ok: true; data: unknown } | { ok: false; error: string; status?: number };

  if (body.action === "upsert-role") {
    const name = typeof body.name === "string" ? body.name.trim() : "";
    const permissions = body.permissions;

    // Multi-org selector: accepts `orgIds` (an array -- the current
    // shape) or falls back to the legacy single `orgId` string for any
    // caller not yet updated. Neither present defaults to a one-element
    // set of DEFAULT_ORG_ID, matching the previous single-org default.
    let orgIds: string[];
    if (
      Array.isArray(body.orgIds) &&
      body.orgIds.every((v): v is string => typeof v === "string")
    ) {
      orgIds = Array.from(new Set(body.orgIds.map((v) => v.trim()).filter(Boolean)));
    } else if (typeof body.orgId === "string" && body.orgId.trim()) {
      orgIds = [body.orgId.trim()];
    } else {
      orgIds = [DEFAULT_ORG_ID];
    }

    if (!name || orgIds.length === 0 || !isPermissionArray(permissions)) {
      return NextResponse.json(
        {
          error: `name is required, orgIds must be a non-empty array of strings, and permissions must be a subset of: ${PERMISSIONS.join(", ")}`,
        },
        { status: 400 },
      );
    }
    const id = typeof body.id === "string" && body.id.trim() ? body.id.trim() : globalThis.crypto.randomUUID();
    const role: CustomRole = { id, orgIds, name, permissions };
    const upserted = await upsertCustomRole(role);
    result = upserted.ok ? { ok: true, data: upserted.data } : { ok: false, error: upserted.error };
  } else if (body.action === "delete-role") {
    const id = typeof body.id === "string" ? body.id.trim() : "";
    if (!id) {
      return NextResponse.json({ error: "id is required" }, { status: 400 });
    }
    const existing = await getCustomRole(id);
    if (!existing.ok) {
      result = { ok: false, error: existing.error };
    } else if (!existing.data) {
      result = { ok: false, error: `custom role '${id}' not found`, status: 404 };
    } else {
      const deleted = await deleteCustomRole(id);
      result = deleted.ok ? { ok: true, data: deleted.data } : { ok: false, error: deleted.error };
    }
  } else if (body.action === "set-grants") {
    const identifier = typeof body.identifier === "string" ? body.identifier.trim() : "";
    const roleIds = body.roleIds;
    if (
      !identifier ||
      !Array.isArray(roleIds) ||
      !roleIds.every((v): v is string => typeof v === "string")
    ) {
      return NextResponse.json(
        { error: "identifier is required and roleIds must be an array of strings" },
        { status: 400 },
      );
    }
    const granted = await setGrantsFor(identifier, roleIds);
    result = granted.ok ? { ok: true, data: granted.data } : { ok: false, error: granted.error };
  } else {
    return NextResponse.json(
      { error: `unknown action '${body.action}' -- must be one of: upsert-role, delete-role, set-grants` },
      { status: 400 },
    );
  }

  writeAuditLogEntry({
    // org-agnostic: an upsert-role action can target multiple orgIds (orgIds above), and delete-role/set-grants act by id/identifier, not a single orgId
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/roles?action=${body.action}`,
    status: result.ok ? 200 : (result.status ?? 502),
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: result.status ?? 502 });
  }
  return NextResponse.json({ result: result.data });
}
