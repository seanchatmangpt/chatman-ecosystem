import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { runPatchSlaBreachScan, listOpenPatchSlaBreaches } from "@/lib/patch-sla";

// Real, unattended poller endpoint the `app/api/cron/`-convention CronJob
// hits on a schedule (see app/api/cron/retention-purge/route.ts's own
// header comment for the identical shared-secret-header pattern this
// route reuses, and the one-time operator provisioning step: `kubectl
// create secret generic platform-patch-sla-cron-secret
// --from-literal=secret=...` in the `platform-console` namespace, then
// setting PATCH_SLA_BREACH_SCAN_CRON_SECRET on the console's own
// Deployment). Checked BEFORE any session cookie so the CronJob's Pod
// (which carries no session) can reach this route at all.
//
// POST runs the real breach walk (lib/patch-sla.ts's
// runPatchSlaBreachScan): every org with `patchSlaTier` set is scored
// against its own real open findings, and any finding still open past
// its committed remediation window is idempotently recorded as a breach
// -- the input the credit-application route
// (POST /api/orgs/[id]/patch-sla-credits) reads back.
//
// GET is the admin-only, platform-wide "what's currently breaching and
// uncredited" visibility route -- same "owner" floor as
// GET /api/security-scan (the underlying finding data is the same
// sensitivity class).
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.PATCH_SLA_BREACH_SCAN_CRON_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-patch-sla-breach-scan-cron-secret");
  return presented === expected;
}

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const result = await runPatchSlaBreachScan();

  // org-agnostic: platform-wide scan spanning every opted-in org's own
  // breach results (each individually attributed inside `report.results`)
  // -- no single org id to key this top-level audit row to, same
  // convention app/api/cron/retention-purge/route.ts's own audit write
  // already establishes for its own platform-wide action.
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "system:patch-sla-breach-scan",
    method: "POST",
    path: "/api/patch-sla/breaches",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ report: result.data });
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: session.sub,
      method: "GET",
      path: "/api/patch-sla/breaches",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listOpenPatchSlaBreaches();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "GET",
    path: "/api/patch-sla/breaches",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ breaches: result.data });
}
