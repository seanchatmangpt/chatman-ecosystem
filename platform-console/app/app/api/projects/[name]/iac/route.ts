import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { detectDrift, exportProjectManifest } from "@/lib/iac";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// (which lib/iac.ts is built on) reads the ServiceAccount token/CA from
// disk, which the edge runtime cannot do.
//
// Real IaC export + drift detection for one project, GET-only (this module
// never writes anything to the cluster -- it only reads and diffs, the
// same read-only posture CloudFormation drift detection / `terraform
// plan` have).

async function requireActor(request: NextRequest): Promise<string | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  return session?.sub ?? null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const actor = await requireActor(request);
  if (!actor) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const { name } = await params;

  const [manifestResult, driftResult] = await Promise.all([
    exportProjectManifest(name),
    detectDrift(name),
  ]);

  // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/projects/${name}/iac`,
    status: manifestResult.ok && driftResult.ok ? 200 : 502,
    requestId,
  });

  if (!manifestResult.ok) {
    const status = /not found/i.test(manifestResult.error) ? 404 : 502;
    return NextResponse.json({ error: manifestResult.error }, { status });
  }
  if (!driftResult.ok) {
    const status = /not found/i.test(driftResult.error) ? 404 : 502;
    return NextResponse.json({ error: driftResult.error }, { status });
  }

  return NextResponse.json({ manifest: manifestResult.data, drift: driftResult.data });
}
