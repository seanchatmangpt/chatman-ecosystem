import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  scanRotationCompliance,
  fileAndApplyRotationComplianceBlocks,
  clearRotationComplianceBlock,
  ROTATION_SLA_DAYS,
} from "@/lib/rotation-compliance";

// Secret & Certificate Rotation Compliance Enforcement -- the maker-
// checker-gated policy that flags/blocks orgs whose real k8s Secrets or
// TLS certificates (already tracked by /api/secrets and
// /api/certificates) have exceeded ROTATION_SLA_DAYS without being
// rotated, writing the durable, audited compliance-violation record a
// security team points auditors at during a SOC2/PCI review. Owner-only
// on every verb, same floor GET/POST /api/security-scan already set for
// a platform-wide, cross-org security posture surface -- this is not a
// per-org viewer-readable resource, it is the operator's own compliance
// control panel.
//
// GET  -- pure, read-only scan (lib/rotation-compliance.ts's
//         scanRotationCompliance). Never files or actuates anything.
// POST -- runs the same scan, then files (or, when a fresh approval
//         already exists, actually applies) a real `compliance.rotation-
//         block` maker-checker approval request per violating org
//         (lib/rotation-compliance.ts's
//         fileAndApplyRotationComplianceBlocks) -- never blocks an org
//         on this route's own say-so; a second, distinct owner-role
//         approver must sign off first via POST /api/approvals/[id].
// DELETE ?orgId=... -- requests clearing an existing block for one org
//         (the org's secrets/certs have since been rotated), same
//         maker-checker gate, never self-cleared.

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
    // org-agnostic: platform-/session-scoped action with no per-tenant org boundary in this route's current data model -- see scripts/check-audit-org-coverage.ts allowlist
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/compliance/rotation",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const scan = await scanRotationCompliance();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/compliance/rotation",
    status: 200,
    requestId,
  });

  return NextResponse.json({ scan, errors: scan.errors });
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
      path: "/api/compliance/rotation",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const scan = await scanRotationCompliance();
  const filings = await fileAndApplyRotationComplianceBlocks(scan, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/compliance/rotation?filed=${filings.length}`,
    status: 200,
    requestId,
  });

  return NextResponse.json({
    scannedAt: scan.scannedAt,
    slaDays: ROTATION_SLA_DAYS,
    errors: scan.errors,
    filings,
  });
}

export async function DELETE(request: NextRequest) {
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
      method: "DELETE",
      path: "/api/compliance/rotation",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgId = request.nextUrl.searchParams.get("orgId") ?? "";
  if (!orgId) {
    return NextResponse.json({ error: "orgId query param is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/compliance/rotation",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const outcome = await clearRotationComplianceBlock(orgResult.data, actor);

  if ("error" in outcome) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/compliance/rotation",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: outcome.error }, { status: 502 });
  }

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/compliance/rotation",
    status: outcome.applied ? 200 : 202,
    requestId,
  });

  if (!outcome.applied) {
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: outcome.approval,
        message:
          "compliance.rotation-block requires a second, distinct owner-role approver -- POST /api/approvals/" +
          `${outcome.approval.requestId} {decision:'approved'} to authorize clearing this org's rotation-` +
          "compliance block, then retry DELETE.",
      },
      { status: 202 },
    );
  }

  return NextResponse.json({ applied: true, orgId, rotationComplianceBlocked: false });
}
