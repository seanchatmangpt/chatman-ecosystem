import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import {
  listSourceEscrowSnapshots,
  requestSourceEscrowSnapshot,
  verifySourceEscrowSnapshot,
  SOURCE_ESCROW_NAMESPACE,
} from "@/lib/source-escrow-attestation";

// Source-Code / Build-Artifact Escrow Attestation -- the maker-checker-
// gated business-continuity/vendor-lock-in artifact (lib/source-escrow-
// attestation.ts) a Fortune-5 legal team's MSA escrow clause points to.
// Owner-only on every verb, same floor GET/POST /api/compliance/rotation
// and GET/POST /api/security-scan/sbom already set for a platform-wide
// compliance-evidence surface -- this is not a per-org viewer-readable
// resource, it is the operator's own compliance control panel.
//
// GET  -- lists every real signed escrow bundle ever generated, newest
//         first. Never mutates anything.
// POST -- collects a fresh real manifest (git commit SHA + Deployments +
//         Flux state + runtime image digests) and requires a
//         `source-escrow.snapshot` maker-checker approval before it is
//         ever signed and persisted -- never signs on this route's own
//         say-so; a second, distinct owner-role approver must sign off
//         first via POST /api/approvals/[id].

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
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    // org-agnostic: this attests to this platform's own release, with no
    // per-tenant org boundary, same allowlisted class as GET
    // /api/compliance/rotation and GET /api/security-scan/sbom -- see
    // scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/compliance/source-escrow",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const verifyParam = request.nextUrl.searchParams.get("verify");
  if (verifyParam) {
    const verification = await verifySourceEscrowSnapshot(verifyParam);
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/compliance/source-escrow?verify=${verifyParam}`,
      status: verification.ok ? 200 : 502,
      requestId,
    });
    if (!verification.ok) {
      return NextResponse.json({ error: verification.error }, { status: 502 });
    }
    return NextResponse.json({ verification: verification.data });
  }

  const result = await listSourceEscrowSnapshots();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/compliance/source-escrow",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ snapshots: result.data });
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
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/compliance/source-escrow",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await requestSourceEscrowSnapshot(actor, SOURCE_ESCROW_NAMESPACE);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/compliance/source-escrow",
    status: result.ok ? (result.data.applied ? 201 : 202) : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  if (!result.data.applied) {
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: result.data.approval,
        message:
          "source-escrow.snapshot requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${result.data.approval.requestId} {decision:'approved'} to authorize signing and escrowing this ` +
          "release snapshot, then retry POST.",
      },
      { status: 202 },
    );
  }

  return NextResponse.json({ applied: true, record: result.data.record }, { status: 201 });
}
