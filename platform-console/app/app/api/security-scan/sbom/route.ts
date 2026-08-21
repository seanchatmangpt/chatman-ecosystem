import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { generateSbomAttestation, listSbomAttestations } from "@/lib/sbom-attestation";

// Real per-deployment SBOM export & CVE-provenance attestation
// (lib/sbom-attestation.ts) -- the NIST SSDF/EO 14028 supply-chain
// artifact, built entirely from data lib/vuln-scan.ts and lib/k8s.ts
// already collect, never a fabricated package list.
//
// Same owner-only floor as POST/GET/DELETE /api/security-scan: this reads
// (and, on POST, signs and durably stores) a security-evidence artifact
// derived from the same scan Job that route already gates at owner, so
// gating this any looser would let a non-owner mint a signed attestation
// off a scan they couldn't have triggered themselves.
//
// POST generates one bundle (one SBOM + one signed attestation per scanned
// image) from an already-COMPLETED vuln-scan job -- never triggers a new
// scan itself; callers pass the `jobName` a prior POST /api/security-scan
// returned. GET lists every bundle ever generated, newest first.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: this attests to a platform-wide scan Job with no
    // per-tenant org boundary, same allowlisted class as
    // POST /api/security-scan itself -- see scripts/check-audit-org-coverage.ts
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/security-scan/sbom",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "invalid JSON body" }, { status: 400 });
  }
  const jobName = (body as { jobName?: unknown } | null)?.jobName;
  if (typeof jobName !== "string" || jobName.length === 0) {
    return NextResponse.json({ error: "jobName is required" }, { status: 400 });
  }

  const result = await generateSbomAttestation(jobName, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/security-scan/sbom",
    status: result.ok ? 200 : 400,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json(result.data);
}

export async function GET(request: NextRequest) {
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const access = await requireRole(session, "owner");
  if (!access.ok) return access.response!;

  const result = await listSbomAttestations();
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ bundles: result.data });
}
