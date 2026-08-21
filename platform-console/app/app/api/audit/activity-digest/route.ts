import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import {
  newRequestId,
  queryOrgActivityDigest,
  renderOrgActivityDigestMarkdown,
  writeAuditLogEntry,
} from "@/lib/audit-db";
import { listActivityDigestSnapshots } from "@/lib/audit-digest-history";
import { requireRole } from "@/lib/authz";

// Real customer-facing weekly team-activity AUDIT DIGEST -- the distinct,
// smaller deliverable this closes: queryAuditLog/queryAuditLogSince
// (GET /api/audit, GET /api/v1/audit-export) already give a compliance
// officer real, row-level, hash-chained audit access, but a Fortune-5
// buyer's compliance officer filing weekly evidence does not want to
// read raw rows or stand up SIEM tooling -- they want "who did what this
// week," summarized and human-readable, in one request. This route
// computes exactly that, on demand, via lib/audit-db.ts's
// queryOrgActivityDigest (a summarization query over the SAME
// platform_console.audit_log rows /audit and the SIEM export already
// read -- no new table).
//
// Auth: session-cookie only (same as GET /api/audit), owner-gated the
// SAME way GET /api/audit already is -- who-did-what visibility,
// summarized or not, is exactly as sensitive as the raw rows it's
// derived from, so this route inherits that route's access floor rather
// than inventing a laxer one.
//
// `orgId` (required): the org this digest is scoped to -- there is no
// unscoped/platform-wide digest, matching queryOrgActivityDigest's own
// contract.
// `sinceDate` (optional): RFC3339 lower bound of the digest window;
// defaults to 7 days ago (the "weekly" in this capability's name) so the
// common case ("this week's digest") needs no query params beyond
// orgId.
// `format=markdown` (optional): returns the Markdown/plain-text
// rendering directly as `text/markdown`, the artifact a compliance
// officer pastes straight into a review ticket -- default response is
// JSON (the grouped digest PLUS the same markdown rendering, so a caller
// that wants to build its own UI never has to re-derive it).
// `history=true` (optional): instead of computing a fresh digest,
// returns the persisted snapshot history POST /api/cron/audit-activity-
// digest already wrote for this org via lib/audit-digest-history.ts --
// "what did last week's filed digest actually say," not a live
// recomputation.
//
// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// and the `pg` driver lib/audit-db.ts uses both need it, same as every
// other audit-db.ts-backed route.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;

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
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/audit/activity-digest",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const params = request.nextUrl.searchParams;
  const orgId = params.get("orgId")?.trim();
  if (!orgId) {
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  if (params.get("history") === "true") {
    const historyResult = await listActivityDigestSnapshots(orgId);
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/audit/activity-digest",
      status: historyResult.ok ? 200 : 502,
      requestId,
    });
    if (!historyResult.ok) {
      return NextResponse.json({ error: historyResult.error }, { status: 502 });
    }
    return NextResponse.json({ orgId, snapshots: historyResult.data });
  }

  const sinceParam = params.get("sinceDate")?.trim();
  const sinceDate = sinceParam || new Date(Date.now() - SEVEN_DAYS_MS).toISOString();
  if (Number.isNaN(new Date(sinceDate).getTime())) {
    return NextResponse.json({ error: "sinceDate must be a valid RFC3339 timestamp" }, { status: 400 });
  }

  const digestResult = await queryOrgActivityDigest(orgId, sinceDate);

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/audit/activity-digest",
    status: digestResult.ok ? 200 : 502,
    requestId,
  });

  if (!digestResult.ok) {
    return NextResponse.json({ error: digestResult.error }, { status: 502 });
  }

  const markdown = renderOrgActivityDigestMarkdown(digestResult.data);

  if (params.get("format") === "markdown") {
    return new NextResponse(markdown, {
      status: 200,
      headers: { "content-type": "text/markdown; charset=utf-8" },
    });
  }

  return NextResponse.json({ digest: digestResult.data, markdown });
}
