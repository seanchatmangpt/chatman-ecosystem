import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { getDeploymentScorecard } from "@/lib/k8s";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Per-project change-failure-rate / deployment-health scorecard (DORA
// Change Failure Rate + MTTR): the environment-promotion pipeline
// (app/api/projects/[name]/promote) and change-freeze windows
// (lib/freeze-windows.ts) already track and gate individual changes, but
// neither aggregates outcomes over time into the standard metric pair
// Fortune-5 platform-engineering leadership reports to their own
// executives. This route is a pure read: getDeploymentScorecard
// (lib/k8s.ts) computes both numbers fresh on every call from this
// project's own real Jobs and lib/incidents.ts's own real incident rows
// -- no new persistence, same "computed fresh, never cached across
// requests" convention every other real-time dashboard read in this
// console already uses (e.g. lib/dashboards.ts's executeWidget, this
// module's own lib/status-page.ts).
//
// Auth: any authenticated member of the caller's org, floor "viewer" --
// same read-only boundary lib/freeze-windows.ts's GET already uses for
// "seeing an aggregate posture number is not a privileged action."
// Bearer API-key auth resolves to the same session cookie before this
// route ever runs (middleware.ts's Node-runtime resolveApiKeyAuth path),
// so this handler needs no separate API-key branch.

const DEFAULT_WINDOW_DAYS = 30;
const MIN_WINDOW_DAYS = 1;
const MAX_WINDOW_DAYS = 365;

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
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
  const actor = roleIdentifierFor(session);
  const { name } = await params;

  const access = await requireRole(session, "viewer");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/projects/${name}/deployment-scorecard`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const windowDaysRaw = request.nextUrl.searchParams.get("windowDays");
  const windowDays = windowDaysRaw !== null ? Number(windowDaysRaw) : DEFAULT_WINDOW_DAYS;
  if (
    !Number.isInteger(windowDays) ||
    windowDays < MIN_WINDOW_DAYS ||
    windowDays > MAX_WINDOW_DAYS
  ) {
    return NextResponse.json(
      {
        error: `windowDays must be an integer between ${MIN_WINDOW_DAYS} and ${MAX_WINDOW_DAYS}`,
      },
      { status: 400 },
    );
  }

  const result = await getDeploymentScorecard(name, windowDays);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/projects/${name}/deployment-scorecard`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    const status = /not found$/.test(result.error) ? 404 : 502;
    return NextResponse.json({ error: result.error }, { status });
  }

  const scorecard = result.data;
  return NextResponse.json({
    windowDays: scorecard.windowDays,
    windowStart: scorecard.windowStart,
    windowEnd: scorecard.windowEnd,
    totalDeploys: scorecard.totalDeploys,
    failedDeploys: scorecard.failedDeploys,
    changeFailureRate: scorecard.changeFailureRate,
    mttrMinutes: scorecard.mttrMinutes,
    resolvedIncidentCount: scorecard.resolvedIncidentCount,
    projectName: scorecard.projectName,
    namespace: scorecard.namespace,
  });
}
