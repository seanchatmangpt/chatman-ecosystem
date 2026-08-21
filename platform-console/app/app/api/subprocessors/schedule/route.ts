import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { generateDpaSubprocessorSchedule } from "@/lib/subprocessors";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";

// Real, live-rendered DPA Sub-processor Schedule document -- the exact
// text an enterprise legal team's own DPA template attaches verbatim,
// computed from this registry's own current active state
// (lib/subprocessors.ts's generateDpaSubprocessorSchedule), never a
// hand-maintained document that can drift from what
// GET /api/subprocessors itself shows. Read-only: any authenticated
// session (member and up) may fetch it, same floor GET /api/subprocessors
// already sets -- a customer's own legal/procurement contact routinely
// needs this document, and reading it changes no state.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/subprocessors/schedule",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await generateDpaSubprocessorSchedule();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/subprocessors/schedule",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  const format = request.nextUrl.searchParams.get("format");
  if (format === "text") {
    return new NextResponse(result.data, {
      status: 200,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }
  return NextResponse.json({ schedule: result.data });
}
