import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import { getOrg } from "@/lib/orgs";
import {
  INSURANCE_COVERAGE_TYPES,
  generateInsuranceAttestation,
  listInsuranceAttestations,
  listInsurancePolicies,
  recordInsurancePolicyVersion,
  renderInsuranceAttestationPdf,
  type InsuranceCoverageType,
  type InsurancePolicyRecord,
} from "@/lib/insurance-attestation";

// Real, owner-gated Certificate of Insurance (COI) On-Demand Attestation
// endpoint -- see lib/insurance-attestation.ts's own header comment for
// the full scope (storage/versioning/maker-checker/PDF-rendering).
//
// Auth model, same "platform owner, not merely an org-role owner" bar
// GET/PUT /api/owner/le-requests and GET/POST /api/owner/security-
// questionnaire already set (lib/authz.ts's requireRole, not
// requireRoleIn) -- the platform's own insurance posture is a
// platform-operations fact, not something a customer org's own "owner"
// role can self-serve or self-attest to:
//   - GET: lists the current policy registry (default), or, with
//     ?history=1, the history of every generated attestation manifest.
//   - PUT: records a new/renewed policy version, gated behind the SAME
//     maker-checker `insurance.policy.update` approval workflow
//     `subprocessor.registry.update`/`denied-party.override` already use
//     -- one platform owner's own say-so is never sufficient by itself
//     to change what this platform attests to a counterparty.
//   - POST: read-only -- generates a fresh attestation PDF from the
//     already-recorded, already-approved current policy registry and
//     streams it back directly, same "no separate signed-download-URL
//     hop" posture POST /api/owner/security-questionnaire already
//     establishes.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isCoverageType(value: unknown): value is InsuranceCoverageType {
  return typeof value === "string" && (INSURANCE_COVERAGE_TYPES as string[]).includes(value);
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
      path: "/api/owner/insurance-attestation",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const wantsHistory = request.nextUrl.searchParams.get("history") === "1";

  if (wantsHistory) {
    const result = await listInsuranceAttestations();
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/insurance-attestation?history=1",
      status: result.ok ? 200 : 502,
      requestId,
    });
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
    return NextResponse.json({ attestations: result.data });
  }

  const result = await listInsurancePolicies();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/owner/insurance-attestation",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ policies: result.data });
}

export async function PUT(request: NextRequest) {
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
      method: "PUT",
      path: "/api/owner/insurance-attestation",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const b = body as Record<string, unknown> | null;

  const coverageType = b?.coverageType;
  const carrier = typeof b?.carrier === "string" ? b.carrier.trim() : "";
  const policyNumber = typeof b?.policyNumber === "string" ? b.policyNumber.trim() : "";
  const coverageLimitUsd = typeof b?.coverageLimitUsd === "number" ? b.coverageLimitUsd : NaN;
  const effectiveDate = typeof b?.effectiveDate === "string" ? b.effectiveDate.trim() : "";
  const expiryDate = typeof b?.expiryDate === "string" ? b.expiryDate.trim() : "";
  const amBestRating = typeof b?.amBestRating === "string" && b.amBestRating.trim() ? b.amBestRating.trim() : undefined;

  if (
    !isCoverageType(coverageType) ||
    !carrier ||
    !policyNumber ||
    !Number.isFinite(coverageLimitUsd) ||
    coverageLimitUsd <= 0 ||
    !effectiveDate ||
    Number.isNaN(Date.parse(effectiveDate)) ||
    !expiryDate ||
    Number.isNaN(Date.parse(expiryDate))
  ) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/insurance-attestation",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "coverageType (cyber|errors_omissions|general_liability), carrier, policyNumber, " +
          "coverageLimitUsd (>0), effectiveDate, and expiryDate (valid dates) are all required",
      },
      { status: 400 },
    );
  }
  if (Date.parse(expiryDate) <= Date.parse(effectiveDate)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/insurance-attestation",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "expiryDate must be after effectiveDate" }, { status: 400 });
  }

  const record: InsurancePolicyRecord = {
    coverageType,
    carrier,
    policyNumber,
    coverageLimitUsd,
    effectiveDate,
    expiryDate,
    ...(amBestRating ? { amBestRating } : {}),
  };

  const approval = await requireApproval({
    action: "insurance.policy.update",
    targetId: coverageType,
    requestedBy: actor,
    resourcePayload: { requestedInsurancePolicy: record },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/insurance-attestation",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/insurance-attestation",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "insurance.policy.update requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize recording this ` +
          "policy version, then retry PUT.",
      },
      { status: 202 },
    );
  }

  // Bind exactly what was approved, never whatever the retried request
  // body happens to say now -- same "bind exactly what was approved"
  // discipline PUT /api/orgs/[id]/pricing-override already establishes.
  const approvedRecord = approval.approval.resourcePayload?.requestedInsurancePolicy;
  if (!approvedRecord) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/insurance-attestation",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: "approved request is missing its policy payload" }, { status: 502 });
  }

  const recorded = await recordInsurancePolicyVersion({
    record: approvedRecord,
    recordedByIdentifier: approval.approval.approvedBy ?? actor,
    requestedByIdentifier: approval.approval.requestedBy,
  });

  if (!recorded.ok) {
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/insurance-attestation",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: recorded.error }, { status: 502 });
  }

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: "/api/owner/insurance-attestation",
    status: 200,
    requestId,
    insuranceAction: "policy_recorded",
    insuranceCoverageType: approvedRecord.coverageType,
  });

  return NextResponse.json({
    recorded: true,
    version: recorded.data,
    approvedBy: approval.approval.approvedBy,
  });
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
      path: "/api/owner/insurance-attestation",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => ({}) as unknown);
  const orgIdInput = (body as { orgId?: unknown } | null)?.orgId;
  if (orgIdInput !== undefined && typeof orgIdInput !== "string") {
    return NextResponse.json({ error: "orgId, when given, must be a string" }, { status: 400 });
  }
  const orgId = typeof orgIdInput === "string" && orgIdInput.length > 0 ? orgIdInput : null;

  let org = null;
  if (orgId) {
    const orgResult = await getOrg(orgId);
    if (!orgResult.ok) {
      writeAuditLogEntry({
        orgId,
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: "/api/owner/insurance-attestation",
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
        path: "/api/owner/insurance-attestation",
        status: 404,
        requestId,
      });
      return NextResponse.json({ error: "org not found" }, { status: 404 });
    }
    org = orgResult.data;
  }

  const result = await generateInsuranceAttestation(orgId, actor);

  writeAuditLogEntry({
    ...(orgId ? { orgId } : {}),
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/owner/insurance-attestation${orgId ? `?orgId=${encodeURIComponent(orgId)}` : ""}`,
    status: result.ok ? 200 : 400,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }

  await writeAuditLogEntryAwaited({
    ...(orgId ? { orgId } : {}),
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/owner/insurance-attestation${orgId ? `?orgId=${encodeURIComponent(orgId)}` : ""}`,
    status: 200,
    requestId: newRequestId(),
    insuranceAction: "attestation_generated",
    insuranceAttestationId: result.data.manifest.id,
  });

  const pdf = renderInsuranceAttestationPdf({ manifest: result.data.manifest, policies: result.data.policies, org });
  const stamp = result.data.manifest.generatedAt.replace(/[:.]/g, "-");
  const filename = `certificate-of-insurance${org ? `-${org.id}` : ""}-${stamp}.pdf`;

  return new NextResponse(new Uint8Array(pdf), {
    status: 200,
    headers: {
      "content-type": "application/pdf",
      "cache-control": "private, no-store",
      "content-disposition": `attachment; filename="${filename}"`,
      "x-insurance-attestation-id": result.data.manifest.id,
    },
  });
}
