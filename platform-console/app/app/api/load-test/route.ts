import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { LOAD_TEST_TARGETS, runLoadTestAgainstTarget } from "@/lib/load-test";

// Runs on the Node.js runtime (default for route handlers) -- lib/audit-db.ts's
// `pg` driver requires it, same reasoning every other /api/* route documents.
//
// GET just lists the fixed target allowlist (read-only, no real load
// generated) -- any authenticated session may see it. POST actually fires a
// real concurrent-request benchmark against a real internal service: real
// load, real CPU consumed by that service, and (at high enough
// concurrency/duration) a real HorizontalPodAutoscaler scale event -- a
// genuinely consequential action, same class as creating a CronJob or a
// Secret, so it needs at least "member" (lib/authz.ts).

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  return NextResponse.json({
    targets: LOAD_TEST_TARGETS.map((t) => ({ id: t.id, label: t.label })),
  });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "member");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/load-test",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const targetId = typeof body?.targetId === "string" ? body.targetId : "";
  const concurrency = Number(body?.concurrency);
  const durationSec = Number(body?.durationSec);

  if (!targetId) {
    return NextResponse.json(
      { error: `targetId is required, one of: ${LOAD_TEST_TARGETS.map((t) => t.id).join(", ")}` },
      { status: 400 },
    );
  }
  if (!Number.isFinite(concurrency) || concurrency < 1 || concurrency > 300) {
    return NextResponse.json(
      { error: "concurrency must be a number between 1 and 300" },
      { status: 400 },
    );
  }
  if (!Number.isFinite(durationSec) || durationSec < 1 || durationSec > 180) {
    return NextResponse.json(
      { error: "durationSec must be a number between 1 and 180" },
      { status: 400 },
    );
  }

  const result = await runLoadTestAgainstTarget(targetId, { concurrency, durationSec });

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/load-test",
    status: result.ok ? 200 : 400,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json(result.data);
}
