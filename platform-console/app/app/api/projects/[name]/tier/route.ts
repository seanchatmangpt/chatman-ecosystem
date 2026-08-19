import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { getProject, setProjectTier } from "@/lib/k8s";
import { requireRole } from "@/lib/authz";
import { isProjectTier } from "@/lib/tiers";

// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// reads the ServiceAccount token/CA from disk, which the edge runtime
// cannot do.
//
// Real plan-tier change for an existing Project: PATCHes the Project's
// TIER_LABEL and re-derives its ResourceQuota via setProjectTier
// (lib/k8s.ts), so an upgrade/downgrade takes live effect on the quota
// immediately -- same owner-only RBAC boundary as creating/deleting a
// Project (this changes what a namespace is entitled to consume, the
// same class of infrastructure decision).

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> },
) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;
  const { name } = await params;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/tier`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const tier = typeof body?.tier === "string" ? body.tier.trim() : "";
  if (!tier || !isProjectTier(tier)) {
    return NextResponse.json(
      { error: `invalid tier '${tier}' -- must be starter, pro, or enterprise` },
      { status: 400 },
    );
  }

  const projectResult = await getProject(name);
  if (!projectResult.ok) {
    return NextResponse.json({ error: projectResult.error }, { status: 502 });
  }
  if (!projectResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/projects/${name}/tier`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `project '${name}' not found` }, { status: 404 });
  }

  const result = await setProjectTier(name, projectResult.data.namespace, tier);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/projects/${name}/tier`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ project: result.data });
}
