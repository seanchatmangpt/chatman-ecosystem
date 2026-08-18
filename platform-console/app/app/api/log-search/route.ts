import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { buildLogQL, queryLoki } from "@/lib/loki";

// Real cross-pod/cross-namespace log search, backed by the Loki instance
// k8s/loki-log-aggregation.yaml deploys (Promtail DaemonSet -> Loki, both
// in `monitoring`) -- the centralized-log-aggregation control every
// hyperscaler PaaS ships (AWS CloudWatch Logs Insights, GCP Cloud Logging,
// Azure Log Analytics) that /logs's per-pod kubectl-logs tail cannot do.
// Viewer+ (requireRole "viewer"), matching /tracing's read-visibility
// boundary -- log search is operational telemetry, not an access record
// like /audit.
//
// Runs on the Node.js runtime (default for route handlers).

async function requireActor(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const MAX_LIMIT = 500;

export async function GET(request: NextRequest) {
  const session = await requireActor(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const access = await requireRole(session, "viewer");
  if (!access.ok) {
    return access.response!;
  }

  const params = request.nextUrl.searchParams;
  const namespace = params.get("namespace")?.trim() || undefined;
  const pod = params.get("pod")?.trim() || undefined;
  const container = params.get("container")?.trim() || undefined;
  const search = params.get("search")?.trim() || undefined;

  const limitParam = Number(params.get("limit"));
  const limit =
    Number.isFinite(limitParam) && limitParam > 0
      ? Math.min(Math.floor(limitParam), MAX_LIMIT)
      : 200;

  const hoursParam = Number(params.get("hours"));
  const hours = Number.isFinite(hoursParam) && hoursParam > 0 ? Math.min(hoursParam, 168) : 1;

  const logql = buildLogQL({ namespace, pod, container, search });
  const result = await queryLoki(logql, limit, hours);

  if (!result.ok) {
    return NextResponse.json({ error: result.error, logql }, { status: 502 });
  }
  return NextResponse.json({ entries: result.data, logql });
}
