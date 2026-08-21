import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { verifySbomAttestation } from "@/lib/sbom-attestation";

// Tamper-evidence check for one SBOM/attestation bundle: recomputes each
// entry's SBOM digest and HMAC signature from its own stored fields
// (lib/sbom-attestation.ts's verifySbomAttestation) and confirms both
// still match what was actually signed. Same owner-only floor as the rest
// of /api/security-scan.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ sbomId: string }> },
) {
  const { sbomId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/security-scan/sbom/${sbomId}/verify`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await verifySbomAttestation(sbomId);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/security-scan/sbom/${sbomId}/verify`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json(result.data);
}
