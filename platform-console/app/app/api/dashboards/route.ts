import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getRoleFor, roleIdentifierFor, ROLES, type Role } from "@/lib/authz";
import {
  createWidget,
  deleteWidget,
  executeWidget,
  listWidgets,
  minRoleForCreating,
  minRoleForViewing,
  WIDGET_TYPES,
  type Widget,
  type WidgetType,
} from "@/lib/dashboards";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// and lib/audit-db.ts's `pg` driver both need it, same as every other
// route in this console.
//
// No single fixed role gates this whole route: a "Custom Dashboard" is a
// personal collection of saved queries, and each query's real access
// level is exactly what its underlying data source already requires --
// see lib/dashboards.ts's header comment. GET only ever executes a
// widget the caller's OWN role can view (minRoleForViewing); POST only
// ever creates a widget the caller's role can create (minRoleForCreating,
// floor "member"); DELETE only ever removes a widget the caller owns.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function roleMeets(role: Role, minimum: Role): boolean {
  return ROLES.indexOf(role) >= ROLES.indexOf(minimum);
}

interface WidgetWithResult extends Widget {
  result: Awaited<ReturnType<typeof executeWidget>>;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const identifier = roleIdentifierFor(session);
  const role = await getRoleFor(session);

  const listed = await listWidgets(identifier);

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: identifier,
    method: "GET",
    path: "/api/dashboards",
    status: listed.ok ? 200 : 502,
    requestId,
  });

  if (!listed.ok) {
    return NextResponse.json({ error: listed.error }, { status: 502 });
  }

  // Every widget is re-executed fresh, right now -- never a cached or
  // creation-time result. A widget whose type the caller's CURRENT role no
  // longer meets (e.g. an owner-created audit-query widget viewed after a
  // downgrade to member) is skipped with an explicit forbidden result
  // rather than silently executed past the access boundary.
  const widgets: WidgetWithResult[] = await Promise.all(
    listed.data.map(async (widget): Promise<WidgetWithResult> => {
      if (!roleMeets(role, minRoleForViewing(widget.type))) {
        return {
          ...widget,
          result: {
            ok: false,
            error: `role '${role}' does not meet the required minimum role '${minRoleForViewing(widget.type)}' to view a '${widget.type}' widget`,
          },
        };
      }
      return { ...widget, result: await executeWidget(widget) };
    }),
  );

  return NextResponse.json({ widgets, role, widgetTypes: WIDGET_TYPES });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const identifier = roleIdentifierFor(session);
  const role = await getRoleFor(session);

  const body = await request.json().catch(() => null);
  const title = typeof body?.title === "string" ? body.title : "";
  const type = typeof body?.type === "string" ? (body.type as WidgetType) : ("" as WidgetType);
  const query = typeof body?.query === "string" ? body.query : "";

  if (!WIDGET_TYPES.includes(type)) {
    return NextResponse.json({ error: `type must be one of: ${WIDGET_TYPES.join(", ")}` }, { status: 400 });
  }

  const requiredRole = minRoleForCreating(type);
  if (!roleMeets(role, requiredRole)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: identifier,
      method: "POST",
      path: "/api/dashboards",
      status: 403,
      requestId,
    });
    return NextResponse.json(
      {
        error: "forbidden",
        reason: `role '${role}' does not meet the required minimum role '${requiredRole}' to create a '${type}' widget`,
      },
      { status: 403 },
    );
  }

  const result = await createWidget({ title, type, query, createdBy: identifier });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: identifier,
    method: "POST",
    path: "/api/dashboards",
    status: result.ok ? 200 : 400,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ widget: result.data });
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const identifier = roleIdentifierFor(session);

  const id = request.nextUrl.searchParams.get("id") ?? "";
  if (!id) {
    return NextResponse.json({ error: "id query param is required" }, { status: 400 });
  }

  const result = await deleteWidget(id, identifier);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: identifier,
    method: "DELETE",
    path: "/api/dashboards",
    status: result.ok ? 200 : 404,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 404 });
  }
  return NextResponse.json({ ok: true });
}
