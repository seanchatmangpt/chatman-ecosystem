import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { CASTLE_DEFAULT_IMAGE, deployCastle } from "@/lib/castle";

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

/**
 * DEPLOY: owner-only (installing a new workload image cluster-side is the
 * same sensitivity class as creating infrastructure, higher than "member"
 * self-service actions like RUN) -- see lib/authz.ts's Role model.
 * Records the already-built, already-`kind load docker-image`d image
 * (/Users/sac/castle/load-castle-image.sh) as this namespace's deployed
 * castle image. Does not build or load the image itself -- that is a
 * real host-level build step outside this Next.js process's own
 * privileges (no Docker socket access from the pod).
 */
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/castle/deploy",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const image =
    typeof body?.image === "string" && body.image.trim() ? body.image.trim() : CASTLE_DEFAULT_IMAGE;

  const result = await deployCastle(image, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/castle/deploy",
    status: result.ok ? 201 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ deployment: result.data }, { status: 201 });
}
