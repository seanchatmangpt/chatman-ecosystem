import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { exportProjectBundle } from "@/lib/export-all";
import { storeExportArchive } from "@/lib/export-download-cache";

// Real "export everything for this tenant" offboarding bundle -- closes
// the gap iac-export-reappliable-and-drift-detected explicitly does not
// cover (it exports only the Project/SingleDatabase manifest shape, never
// row data, storage contents, or audit history). This route triggers the
// exact same pg_dump backup Job the Database Backups module already runs,
// reads its real dump back out of the cluster, lists+downloads every real
// object across every real storage bucket, and pulls the same real
// audit-log NDJSON export GET /api/audit/export already produces --
// bundles the three real artifacts into one zip (lib/zip.ts) and hands
// back one signed, time-boxed download link (lib/export-download-cache.ts),
// rather than three separate manual downloads.
//
// Owner-gated: this is a strictly more sensitive action than any of its
// three constituent parts (full DB dump + full storage contents + full
// audit history, all in one artifact), so it gets at least the same
// "owner" floor GET /api/audit/export and POST /api/exec already use.
//
// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts,
// lib/audit-export.ts (the `pg` driver), and lib/zip.ts's zlib usage all
// need it.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
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
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/export-all`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await exportProjectBundle(name);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/projects/${name}/export-all`,
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    const status = /not found/i.test(result.error) ? 404 : 502;
    return NextResponse.json({ error: result.error }, { status });
  }

  const identifier = roleIdentifierFor(session);
  const signed = storeExportArchive(result.data.archive, result.data.filename, identifier, 15 * 60);
  const downloadUrl = `/api/projects/${encodeURIComponent(name)}/export-all/download?token=${encodeURIComponent(signed.token)}`;

  return NextResponse.json(
    {
      url: downloadUrl,
      expiresAt: signed.expiresAt,
      filename: result.data.filename,
      archiveBytes: result.data.archive.length,
      summary: result.data.summary,
    },
    { status: 201 },
  );
}
