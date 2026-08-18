import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { applyMigration, listMigrations, rollbackMigration } from "@/lib/migrations";

// Runs on the Node.js runtime (default for route handlers) -- lib/migrations.ts's
// `pg` driver needs Node.js `net`/`tls`, same reason lib/audit-db.ts is kept
// out of middleware.ts (see that module's header comment).
//
// Owner-gated (requireRole "owner"), NOT just member+ like Backups' own
// run/restore actions: unlike a backup/restore (which replays data this
// project already produced), a schema migration lets an operator submit
// arbitrary DDL/DML against the project's live database -- the same
// "consequential enough to need the top role" reasoning /org and /audit
// already apply.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const { name } = await params;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/projects/${name}/migrations`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listMigrations(name);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/projects/${name}/migrations`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ migrations: result.data });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const { name } = await params;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/migrations`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = (await request.json().catch(() => ({}))) as Record<string, unknown>;
  const action = typeof body?.action === "string" ? body.action : "apply";

  if (action === "rollback") {
    const version = Number(body?.version);
    const confirm = typeof body?.confirm === "string" ? body.confirm : "";
    if (!Number.isFinite(version)) {
      return NextResponse.json({ error: "version is required" }, { status: 400 });
    }
    if (confirm !== String(version)) {
      return NextResponse.json(
        { error: "confirmation text does not match the migration version -- rollback refused" },
        { status: 400 },
      );
    }

    const result = await rollbackMigration(name, version);

    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/migrations (rollback v${version})`,
      status: result.ok ? 200 : 502,
      requestId,
    });

    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
    return NextResponse.json({ rolledBack: result.data });
  }

  const version = Number(body?.version);
  const migName = typeof body?.name === "string" ? body.name.trim() : "";
  const upSql = typeof body?.upSql === "string" ? body.upSql : "";
  const downSql = typeof body?.downSql === "string" ? body.downSql : "";

  if (!Number.isFinite(version) || !Number.isInteger(version) || version <= 0) {
    return NextResponse.json({ error: "version must be a positive integer" }, { status: 400 });
  }
  if (!migName) {
    return NextResponse.json({ error: "name is required" }, { status: 400 });
  }
  if (!upSql.trim()) {
    return NextResponse.json({ error: "upSql is required" }, { status: 400 });
  }
  if (!downSql.trim()) {
    return NextResponse.json({ error: "downSql is required" }, { status: 400 });
  }

  const result = await applyMigration(name, { version, name: migName, upSql, downSql });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/projects/${name}/migrations (apply v${version})`,
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ migration: result.data }, { status: 201 });
}
