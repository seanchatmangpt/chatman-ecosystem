import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import { listManagedCertificates, rotateCertificate } from "@/lib/cert-lifecycle";

// Backs the owner-only /certificates page -- real Certificate Lifecycle
// tracking (AWS ACM auto-renewal / GCP-managed-certificate rotation
// equivalent). GET is owner-gated for the same reason /api/custom-domains's
// GET already is: cert subject/issuer/serial detail is more than a
// read-mostly resource, and this dashboard exists specifically for the
// operator who ALSO holds rotation power over it. POST rotates one real
// custom-domain certificate's Secret in place -- a real, consequential
// mutation of live TLS material -- held to the exact same "owner" floor
// registerCustomDomain/unbindCustomDomain already are. Runs on the Node.js
// runtime (default for route handlers) -- lib/cert-lifecycle.ts shells out
// to a real openssl subprocess via lib/custom-domains.ts and reads the
// ServiceAccount token from disk via lib/k8s.ts, neither of which the edge
// runtime can do.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
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
      method: "GET",
      path: "/api/certificates",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listManagedCertificates();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/certificates",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ certificates: result.data });
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  // Rotating a live custom-domain certificate in place -- a real fresh
  // openssl-generated cert immediately swapped into a Secret Envoy/SDS is
  // actively serving -- is owner-gated, same requireRole boundary as
  // registering/unbinding a domain in the first place.
  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/certificates",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const secretName = typeof body?.secretName === "string" ? body.secretName.trim() : "";
  if (!secretName) {
    return NextResponse.json({ error: "secretName is required" }, { status: 400 });
  }

  const result = await rotateCertificate(secretName);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/certificates",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ rotation: result.data });
}
