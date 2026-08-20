import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import { getOrg } from "@/lib/orgs";
import { getBackupPolicy } from "@/lib/backup-retention";
import {
  getDataDestructionCertificate,
  issueDataDestructionCertificate,
  listDataDestructionCertificates,
  verifyDataDestruction,
  verifyDataDestructionCertificate,
} from "@/lib/data-destruction-certificate";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";

// Real, session-authed Certificate of Data Destruction endpoints -- see
// lib/data-destruction-certificate.ts's own header comment for the full
// scope (what PVCs/backups/exports/logs mean here, and what is
// deliberately NOT deleted/attested).
//
// Auth model, same "platform owner, not merely an org-role owner" bar
// GET/PUT /api/owner/le-requests already sets (lib/authz.ts's
// requireRole, not requireRoleIn) -- this document is issued BY the
// platform TO a terminating customer, so filing and approving it is a
// platform-operations act, not something the customer's own org-scoped
// "owner" role can self-serve:
//   - GET: platform "owner" -- lists this org's certificates (?orgId=),
//     or fetches and tamper-verifies one specific certificate
//     (?certificateId=).
//   - POST: platform "owner", gated behind the SAME maker-checker
//     `data-destruction.certificate.issue` approval workflow
//     `le-request.respond`/`subprocessor.registry.update` already use --
//     one platform owner's own say-so is never sufficient by itself to
//     mint a certificate finance/legal/security will hand to a customer.
//     Re-verifies teardown state fresh at BOTH filing time (so the
//     second approver reviews real numbers) and issuance time (so a
//     certificate is never minted against a stale verification -- PVCs
//     or backups could theoretically reappear between request and
//     approval) -- issueDataDestructionCertificate itself additionally
//     refuses server-side unless that fresh verification is all-clear,
//     so this route's own re-check is defense in depth, not the only
//     gate.

async function requireSession(request: NextRequest) {
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
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/data-destruction",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const certificateId = request.nextUrl.searchParams.get("certificateId")?.trim();
  if (certificateId) {
    const certResult = await getDataDestructionCertificate(certificateId);
    if (!certResult.ok) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: "/api/owner/data-destruction",
        status: 502,
        requestId,
      });
      return NextResponse.json({ error: certResult.error }, { status: 502 });
    }
    if (!certResult.data) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: "/api/owner/data-destruction",
        status: 404,
        requestId,
      });
      return NextResponse.json({ error: "no such certificate" }, { status: 404 });
    }

    const tamperResult = await verifyDataDestructionCertificate(certificateId);
    writeAuditLogEntry({
      orgId: certResult.data.orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/data-destruction",
      status: tamperResult.ok ? 200 : 502,
      requestId,
    });
    if (!tamperResult.ok) {
      return NextResponse.json({ error: tamperResult.error }, { status: 502 });
    }
    return NextResponse.json({ certificate: certResult.data, integrity: tamperResult.data });
  }

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim();
  if (!orgId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/data-destruction",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "orgId or certificateId query parameter is required" }, { status: 400 });
  }

  const result = await listDataDestructionCertificates(orgId);
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/owner/data-destruction",
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
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const orgId = typeof (body as Record<string, unknown> | null)?.orgId === "string"
    ? (body as Record<string, string>).orgId.trim()
    : "";
  if (!orgId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "orgId is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const namespace = orgResult.data.namespace;

  const verification = await verifyDataDestruction(orgId, namespace);
  if (!verification.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: verification.error }, { status: 502 });
  }

  const approval = await requireApproval({
    action: "data-destruction.certificate.issue",
    targetId: orgId,
    requestedBy: actor,
    resourcePayload: {
      requestedDataDestruction: {
        namespace: verification.data.namespace,
        namespaceExists: verification.data.namespaceExists,
        remainingPvcNames: verification.data.remainingPvcNames,
        backupRecordsUndeleted: verification.data.backupRecordsUndeleted,
      },
    },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        verification: verification.data,
        message:
          "data-destruction.certificate.issue requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize issuing this ` +
          "certificate, then retry POST.",
      },
      { status: 202 },
    );
  }

  // Fresh re-check at issuance time -- never trust the (possibly hours-
  // old, per APPROVAL_TTL_HOURS) verification snapshot the approver
  // actually reviewed; the certificate must attest to what is true right
  // now.
  const freshVerification = await verifyDataDestruction(orgId, namespace);
  if (!freshVerification.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: freshVerification.error }, { status: 502 });
  }

  const policyResult = await getBackupPolicy(orgId);
  const contractRetentionTermsDays = policyResult.ok ? policyResult.data?.retentionDays : undefined;

  const issued = await issueDataDestructionCertificate({
    orgId,
    namespace,
    requestedBy: approval.approval.requestedBy,
    issuedBy: approval.approval.approvedBy ?? actor,
    verification: freshVerification.data,
    ...(contractRetentionTermsDays !== undefined ? { contractRetentionTermsDays } : {}),
  });

  if (!issued.ok) {
    const status = issued.error === "not_all_clear" ? 409 : 502;
    await writeAuditLogEntryAwaited({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/data-destruction",
      status,
      requestId,
    });
    return NextResponse.json(
      {
        error: issued.error,
        message:
          issued.error === "not_all_clear"
            ? "teardown is not yet complete -- refusing to mint a false certificate"
            : issued.error,
        verification: freshVerification.data,
      },
      { status },
    );
  }

  await writeAuditLogEntryAwaited({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/owner/data-destruction",
    status: 200,
    requestId,
  });

  return NextResponse.json({
    issued: true,
    certificate: issued.data,
    approvedBy: approval.approval.approvedBy,
  });
}
