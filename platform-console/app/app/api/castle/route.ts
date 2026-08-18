import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getCastleDeployment, listCastleJobs, getCastleJobOutput } from "@/lib/castle";

// Runs on the Node.js runtime -- lib/k8s.ts reads the ServiceAccount
// token/CA from disk, which the edge runtime cannot do.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

/**
 * View-only GET: current deployment state + every real Run Job this
 * module created. `?logs=<jobName>` additionally fetches that one Job's
 * real captured output. No RBAC gate beyond authentication -- viewing is
 * "member+" per the module's own scope note, but every authenticated
 * session is already at least "viewer", and viewing is deliberately
 * un-gated further, same as every other module's own GET listing route.
 */
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const [deployment, jobs] = await Promise.all([getCastleDeployment(), listCastleJobs()]);

  const logsJobName = request.nextUrl.searchParams.get("logs");
  const logs = logsJobName ? await getCastleJobOutput(logsJobName) : null;

  const ok = deployment.ok && jobs.ok && (!logsJobName || (logs?.ok ?? false));
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/castle",
    status: ok ? 200 : 502,
    requestId,
  });

  if (!deployment.ok) return NextResponse.json({ error: deployment.error }, { status: 502 });
  if (!jobs.ok) return NextResponse.json({ error: jobs.error }, { status: 502 });
  if (logsJobName && logs && !logs.ok) {
    return NextResponse.json({ error: logs.error }, { status: 502 });
  }

  return NextResponse.json({
    deployment: deployment.data,
    jobs: jobs.data,
    ...(logsJobName ? { logs: logs?.ok ? logs.data : null } : {}),
  });
}
