import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { ALLOWED_CASTLE_VERBS, resolveCastleVerb, runCastleVerb } from "@/lib/castle";

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

/**
 * RUN: member+ (self-service, same class as Scheduled Jobs' POST). Only
 * ever triggers a real, already-shipped, read-only castle CLI verb
 * resolved against the fixed ALLOWED_CASTLE_VERBS allowlist
 * (lib/castle.ts) -- `verbId` is the only field this route accepts from
 * the request body, and anything outside the allowlist is rejected below
 * before any k8s API call. There is no `construct`/`gymact` verb in the
 * allowlist and never will be until castle's own CLI ships one for real
 * (VISION.md gap #3) -- this route cannot grant CASTLE "DO" authority, it
 * can only invoke the CLI verbs castle's own binary already exposes.
 */
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/castle/run",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const verbId = typeof body?.verbId === "string" ? body.verbId.trim() : "";
  const verb = resolveCastleVerb(verbId);
  if (!verb) {
    return NextResponse.json(
      { error: `verbId must be one of: ${Object.keys(ALLOWED_CASTLE_VERBS).join(", ")}` },
      { status: 400 },
    );
  }

  const result = await runCastleVerb(verb.id, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/castle/run",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ job: result.data }, { status: 201 });
}
