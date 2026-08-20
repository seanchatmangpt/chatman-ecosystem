import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import { getOrg } from "@/lib/orgs";
import {
  computeVendorOffboardingEvidence,
  getVendorOffboardingAttestation,
  issueVendorOffboardingAttestation,
  listVendorOffboardingAttestations,
  verifyVendorOffboardingAttestation,
  type VendorOffboardingEvidence,
} from "@/lib/vendor-offboarding-attestation";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";

// Real, session-authed Vendor Offboarding Data-Return/Destruction
// Attestation endpoints -- see lib/vendor-offboarding-attestation.ts's own
// header comment for the full scope (what evidence this reads, and the
// fail-closed compliant gate before issuance).
//
// Auth model, same "platform owner, not merely an org-role owner" bar
// GET/POST /api/owner/data-destruction already sets (lib/authz.ts's
// requireRole, not requireRoleIn) -- this document is issued BY the
// platform TO a terminating customer's procurement/legal team, so filing
// and approving it is a platform-operations act, not something the
// customer's own org-scoped "owner" role can self-serve:
//   - GET: platform "owner" -- with `?attestationId=`, fetches and
//     tamper-verifies one specific attestation; with `?orgId=` alone,
//     lists this org's already-issued attestations; with `?orgId=` plus
//     `?terminationDate=`/`?contractualSlaDays=`, computes and returns
//     the LIVE evidence snapshot (no mutation) so a caller can see
//     whether an attestation could be issued right now.
//   - POST: platform "owner", gated behind the SAME maker-checker
//     `vendor-offboarding.attestation.issue` approval workflow
//     `data-destruction.certificate.issue`/`insurance.policy.update`
//     already use -- one platform owner's own say-so is never sufficient
//     by itself to mint a document procurement will hand to legal.
//     Re-computes evidence fresh at BOTH filing time (so the second
//     approver reviews real numbers) and issuance time (so an
//     attestation is never minted against a stale snapshot -- an export
//     or destruction certificate could theoretically land between
//     request and approval) -- issueVendorOffboardingAttestation itself
//     additionally refuses server-side unless that fresh evidence is
//     compliant, so this route's own re-check is defense in depth, not
//     the only gate.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function toApprovalEvidence(evidence: VendorOffboardingEvidence) {
  return {
    terminationDate: evidence.terminationDate,
    contractualSlaDays: evidence.contractualSlaDays,
    slaDeadline: evidence.slaDeadline,
    qualifyingExportRecordIds: evidence.qualifyingExportRecordIds,
    destructionCertificateId: evidence.destructionCertificateId,
    destructionCertificateAllClear: evidence.destructionCertificateAllClear,
    destructionCertificateVerified: evidence.destructionCertificateVerified,
    dataAccountedFor: evidence.dataAccountedFor,
    withinSla: evidence.withinSla,
  };
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
      path: "/api/owner/vendor-offboarding",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const attestationId = request.nextUrl.searchParams.get("attestationId")?.trim();
  if (attestationId) {
    const attResult = await getVendorOffboardingAttestation(attestationId);
    if (!attResult.ok) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: "/api/owner/vendor-offboarding",
        status: 502,
        requestId,
      });
      return NextResponse.json({ error: attResult.error }, { status: 502 });
    }
    if (!attResult.data) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: "/api/owner/vendor-offboarding",
        status: 404,
        requestId,
      });
      return NextResponse.json({ error: "no such attestation" }, { status: 404 });
    }

    const tamperResult = await verifyVendorOffboardingAttestation(attestationId);
    writeAuditLogEntry({
      orgId: attResult.data.orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/vendor-offboarding",
      status: tamperResult.ok ? 200 : 502,
      requestId,
    });
    if (!tamperResult.ok) {
      return NextResponse.json({ error: tamperResult.error }, { status: 502 });
    }
    return NextResponse.json({ attestation: attResult.data, integrity: tamperResult.data });
  }

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim();
  if (!orgId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/vendor-offboarding",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "orgId or attestationId query parameter is required" }, { status: 400 });
  }

  const terminationDate = request.nextUrl.searchParams.get("terminationDate")?.trim();
  const contractualSlaDaysRaw = request.nextUrl.searchParams.get("contractualSlaDays")?.trim();

  if (terminationDate || contractualSlaDaysRaw) {
    if (!terminationDate || Number.isNaN(Date.parse(terminationDate))) {
      writeAuditLogEntry({
        orgId,
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: "/api/owner/vendor-offboarding",
        status: 400,
        requestId,
      });
      return NextResponse.json(
        { error: "terminationDate (a valid date) is required when computing live evidence" },
        { status: 400 },
      );
    }
    const contractualSlaDays = Number(contractualSlaDaysRaw);
    if (!Number.isFinite(contractualSlaDays) || contractualSlaDays <= 0) {
      writeAuditLogEntry({
        orgId,
        timestamp: new Date().toISOString(),
        actor,
        method: "GET",
        path: "/api/owner/vendor-offboarding",
        status: 400,
        requestId,
      });
      return NextResponse.json(
        { error: "contractualSlaDays (a positive number) is required when computing live evidence" },
        { status: 400 },
      );
    }

    const evidence = await computeVendorOffboardingEvidence({ orgId, terminationDate, contractualSlaDays });
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/vendor-offboarding",
      status: evidence.ok ? 200 : 502,
      requestId,
    });
    if (!evidence.ok) {
      return NextResponse.json({ error: evidence.error }, { status: 502 });
    }
    return NextResponse.json({ evidence: evidence.data });
  }

  const result = await listVendorOffboardingAttestations(orgId);
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/owner/vendor-offboarding",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ attestations: result.data });
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
      path: "/api/owner/vendor-offboarding",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const b = body as Record<string, unknown> | null;
  const orgId = typeof b?.orgId === "string" ? b.orgId.trim() : "";
  const terminationDate = typeof b?.terminationDate === "string" ? b.terminationDate.trim() : "";
  const contractualSlaDays = typeof b?.contractualSlaDays === "number" ? b.contractualSlaDays : NaN;

  if (!orgId || !terminationDate || Number.isNaN(Date.parse(terminationDate))) {
    writeAuditLogEntry({
      ...(orgId ? { orgId } : {}),
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/vendor-offboarding",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "orgId and terminationDate (a valid date) are required" },
      { status: 400 },
    );
  }
  if (!Number.isFinite(contractualSlaDays) || contractualSlaDays <= 0) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/vendor-offboarding",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "contractualSlaDays (a positive number) is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/vendor-offboarding",
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
      path: "/api/owner/vendor-offboarding",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const evidence = await computeVendorOffboardingEvidence({ orgId, terminationDate, contractualSlaDays });
  if (!evidence.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/vendor-offboarding",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: evidence.error }, { status: 502 });
  }

  const approval = await requireApproval({
    action: "vendor-offboarding.attestation.issue",
    targetId: orgId,
    requestedBy: actor,
    resourcePayload: {
      requestedVendorOffboardingEvidence: toApprovalEvidence(evidence.data),
    },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/vendor-offboarding",
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
      path: "/api/owner/vendor-offboarding",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        evidence: evidence.data,
        message:
          "vendor-offboarding.attestation.issue requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize issuing this ` +
          "attestation, then retry POST.",
      },
      { status: 202 },
    );
  }

  // Fresh re-check at issuance time -- never trust the (possibly hours-
  // old, per APPROVAL_TTL_HOURS) evidence snapshot the approver actually
  // reviewed; the attestation must attest to what is true right now.
  const freshEvidence = await computeVendorOffboardingEvidence({ orgId, terminationDate, contractualSlaDays });
  if (!freshEvidence.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/vendor-offboarding",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: freshEvidence.error }, { status: 502 });
  }

  const issued = await issueVendorOffboardingAttestation({
    orgId,
    requestedBy: approval.approval.requestedBy,
    issuedBy: approval.approval.approvedBy ?? actor,
    evidence: freshEvidence.data,
  });

  if (!issued.ok) {
    const status = issued.error === "not_compliant" ? 409 : 502;
    await writeAuditLogEntryAwaited({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/vendor-offboarding",
      status,
      requestId,
    });
    return NextResponse.json(
      {
        error: issued.error,
        message:
          issued.error === "not_compliant"
            ? "data return/destruction is not yet complete or not within SLA -- refusing to mint a false attestation"
            : issued.error,
        evidence: freshEvidence.data,
      },
      { status },
    );
  }

  await writeAuditLogEntryAwaited({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/owner/vendor-offboarding",
    status: 200,
    requestId,
    vendorOffboardingAction: "attestation_issued",
    vendorOffboardingAttestationId: issued.data.id,
  });

  return NextResponse.json({
    issued: true,
    attestation: issued.data,
    approvedBy: approval.approval.approvedBy,
  });
}
