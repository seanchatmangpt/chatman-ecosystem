import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import { getOrg } from "@/lib/orgs";
import {
  buildPersonnelRosterSnapshot,
  completePersonnelAttestation,
  getPersonnelAttestationHistory,
  type BackgroundCheckStatus,
  type PersonnelAttestationOverride,
} from "@/lib/personnel-attestation";

// Real, owner-gated Workforce Security-Training & Background-Check
// Attestation endpoint -- see lib/personnel-attestation.ts's own header
// comment for the full scope (roster join, storage, maker-checker).
//
// Auth model, same "platform owner, not merely an org-role owner" bar
// GET/POST /api/owner/insurance-attestation and GET/POST /api/compliance/
// rotation already set (lib/authz.ts's requireRole, not requireRoleIn):
// personnel-control posture is a platform-operations attestation about a
// customer org, not something a customer org's own "owner" role
// self-serves.
//
//   - GET  ?orgId=... (required) -- current roster snapshot (live role
//     assignments joined with real audit-log activity, no
//     training/background-check facts yet applied), or, with
//     ?history=1, this org's full append-only attestation history.
//   - POST -- records a new attestation for one org, gated behind the
//     SAME maker-checker `personnel.attestation.record` approval
//     workflow `insurance.policy.update`/`subprocessor.registry.update`
//     already use -- one platform owner's own say-so is never
//     sufficient by itself to attest a personnel-control posture to a
//     counterparty.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isBackgroundCheckStatus(value: unknown): value is BackgroundCheckStatus {
  return value === "cleared" || value === "pending" || value === "not_required";
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
      path: "/api/compliance/personnel-attestation",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgId = request.nextUrl.searchParams.get("orgId") ?? "";
  if (!orgId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/compliance/personnel-attestation",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/compliance/personnel-attestation",
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
      method: "GET",
      path: "/api/compliance/personnel-attestation",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const wantsHistory = request.nextUrl.searchParams.get("history") === "1";

  if (wantsHistory) {
    const result = await getPersonnelAttestationHistory(orgId);
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/compliance/personnel-attestation?history=1",
      status: result.ok ? 200 : 502,
      requestId,
    });
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
    return NextResponse.json({ history: result.data });
  }

  const result = await buildPersonnelRosterSnapshot(orgId, org.namespace);
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/compliance/personnel-attestation",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ roster: result.data });
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
      path: "/api/compliance/personnel-attestation",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const b = body as Record<string, unknown> | null;

  const orgId = typeof b?.orgId === "string" ? b.orgId.trim() : "";
  const attestationStatement =
    typeof b?.attestationStatement === "string" ? b.attestationStatement.trim() : "";
  const overridesInput = Array.isArray(b?.overrides) ? (b!.overrides as unknown[]) : [];

  if (!orgId || !attestationStatement) {
    writeAuditLogEntry({
      ...(orgId ? { orgId } : {}),
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/compliance/personnel-attestation",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "orgId and attestationStatement are required" },
      { status: 400 },
    );
  }

  const overrides: PersonnelAttestationOverride[] = [];
  for (const raw of overridesInput) {
    const o = raw as Record<string, unknown> | null;
    const identifier = typeof o?.identifier === "string" ? o.identifier.trim() : "";
    if (!identifier || typeof o?.securityTrainingCompleted !== "boolean") {
      writeAuditLogEntry({
        orgId,
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: "/api/compliance/personnel-attestation",
        status: 400,
        requestId,
      });
      return NextResponse.json(
        {
          error:
            "every entry in overrides requires a string identifier and a boolean securityTrainingCompleted",
        },
        { status: 400 },
      );
    }
    const securityTrainingCompletedAt =
      typeof o?.securityTrainingCompletedAt === "string" && o.securityTrainingCompletedAt.trim()
        ? o.securityTrainingCompletedAt.trim()
        : undefined;
    const backgroundCheckStatus = isBackgroundCheckStatus(o?.backgroundCheckStatus)
      ? o.backgroundCheckStatus
      : undefined;
    overrides.push({
      identifier,
      securityTrainingCompleted: o.securityTrainingCompleted,
      ...(securityTrainingCompletedAt ? { securityTrainingCompletedAt } : {}),
      ...(backgroundCheckStatus ? { backgroundCheckStatus } : {}),
    });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/compliance/personnel-attestation",
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
      path: "/api/compliance/personnel-attestation",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }
  const org = orgResult.data;

  const approval = await requireApproval({
    action: "personnel.attestation.record",
    targetId: orgId,
    requestedBy: actor,
    resourcePayload: {
      requestedPersonnelAttestation: { orgId, attestationStatement, overrides },
    },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/compliance/personnel-attestation",
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
      path: "/api/compliance/personnel-attestation",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "personnel.attestation.record requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize recording this ` +
          "attestation, then retry POST.",
      },
      { status: 202 },
    );
  }

  // Bind exactly what was approved, never whatever the retried request
  // body happens to say now -- same "bind exactly what was approved"
  // discipline PUT /api/owner/insurance-attestation already establishes.
  const approvedPayload = approval.approval.resourcePayload?.requestedPersonnelAttestation;
  if (!approvedPayload) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/compliance/personnel-attestation",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: "approved request is missing its attestation payload" }, { status: 502 });
  }

  const recorded = await completePersonnelAttestation({
    orgId,
    namespace: org.namespace,
    attesterIdentifier: approval.approval.approvedBy ?? actor,
    attestationStatement: approvedPayload.attestationStatement,
    overrides: approvedPayload.overrides,
  });

  if (!recorded.ok) {
    await writeAuditLogEntryAwaited({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/compliance/personnel-attestation",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: recorded.error }, { status: 502 });
  }

  await writeAuditLogEntryAwaited({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/compliance/personnel-attestation",
    status: 200,
    requestId,
    personnelAttestationAction: "recorded",
    personnelAttestationTrainingCompletionPercent: recorded.data.record.trainingCompletionPercent,
    personnelAttestationPrivilegedBackgroundCheckClearedPercent:
      recorded.data.record.privilegedBackgroundCheckClearedPercent,
  });

  return NextResponse.json({
    recorded: true,
    record: recorded.data.record,
    approvedBy: approval.approval.approvedBy,
  });
}
