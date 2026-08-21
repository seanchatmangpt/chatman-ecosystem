import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { getSbomAttestation } from "@/lib/sbom-attestation";

// Real single-bundle read -- the JSON an auditor's own in-toto tooling, or
// a Fortune-5 supply-chain review portal, consumes directly (each entry's
// `attestation` field is already a spec-shaped in-toto v1 Statement plus
// its signature envelope). Same owner-only floor as the rest of
// /api/security-scan -- see that route's own header comment.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ sbomId: string }> },
) {
  const { sbomId } = await params;
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const access = await requireRole(session, "owner");
  if (!access.ok) return access.response!;

  const result = await getSbomAttestation(sbomId);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "SBOM/attestation bundle not found" }, { status: 404 });
  }
  return NextResponse.json(result.data);
}
