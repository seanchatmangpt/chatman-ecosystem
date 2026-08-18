import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { queryPrometheus } from "@/lib/prometheus";

const ALLOWED_QUERIES = new Set(["up", "kube_pod_status_ready", "container_memory_working_set_bytes"]);

// A fixed allowlist of PromQL queries, not an open passthrough -- this
// route is reachable by any authenticated console user and Prometheus's
// query language can be used for extraction/DoS-shaped abuse if fully
// open. Extend the allowlist deliberately, not by accepting arbitrary
// client-supplied PromQL.
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const query = request.nextUrl.searchParams.get("query") ?? "up";
  if (!ALLOWED_QUERIES.has(query)) {
    return NextResponse.json(
      { error: `query not in allowlist: ${[...ALLOWED_QUERIES].join(", ")}` },
      { status: 400 },
    );
  }

  const result = await queryPrometheus(query);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: session.sub,
    method: "GET",
    path: "/api/prometheus",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}
