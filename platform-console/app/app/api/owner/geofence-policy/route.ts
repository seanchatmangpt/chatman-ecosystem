import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import { getOrg } from "@/lib/orgs";
import {
  getGeofencePolicy,
  setGeofencePolicy,
  applyGeofenceException,
  checkGeofenceAccess,
  type GeofenceCidrRegion,
  type GeofenceEnforcementMode,
} from "@/lib/geofence-enforcement";

// Real, platform-owner-gated Geofenced Data-Residency Access Enforcement
// endpoint -- see lib/geofence-enforcement.ts's own header comment for
// full scope (storage/region-resolution/maker-checker/exception TTL).
//
// Auth model: same "platform owner, not merely an org-role owner" bar
// GET/PUT /api/owner/insurance-attestation and GET/PUT /api/owner/le-
// requests already set (lib/authz.ts's requireRole, not requireRoleIn)
// -- declaring or reviewing an org's contracted-region ENFORCEMENT
// policy is a security-team/platform-operations decision, not something
// a customer org's own "owner" role self-serves (the customer-visible
// half of this control -- the paper attestation of where their data
// actually landed -- already exists at lib/data-residency-attestation.ts
// / GET /api/orgs/[id]/residency-attestation).
//   - GET: reads the current policy for one org (`?orgId=`). With
//     `?evaluateIp=`, ALSO runs the real enforcement check
//     (`checkGeofenceAccess`) against that IP and durably audit-logs the
//     result (`"access_flagged"`/`"access_rejected"`) -- the concrete
//     tool a security reviewer uses to prove, on demand, "would a
//     request from this IP have been let through or blocked" without
//     waiting for a real violation to occur naturally.
//   - PUT: declares/updates an org's policy shape (contracted regions,
//     CIDR->region map, enforcement mode). NOT gated behind
//     maker-checker, same posture PUT /api/orgs/[id]/ip-allowlist
//     already takes for its own CIDR list -- declaring the policy is not
//     itself the sensitive action.
//   - POST: requests (and, once a second distinct owner approves,
//     applies) a bounded-TTL geofence exception, gated behind the SAME
//     maker-checker `geofence.exception.grant` approval workflow
//     `cmek.key-binding`/`denied-party.override` already use.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const ENFORCEMENT_MODES: GeofenceEnforcementMode[] = ["flag", "reject"];
function isEnforcementMode(value: unknown): value is GeofenceEnforcementMode {
  return typeof value === "string" && (ENFORCEMENT_MODES as string[]).includes(value);
}

function isCidrRegionArray(value: unknown): value is GeofenceCidrRegion[] {
  return (
    Array.isArray(value) &&
    value.every(
      (v) =>
        v &&
        typeof v === "object" &&
        typeof (v as Record<string, unknown>).cidr === "string" &&
        typeof (v as Record<string, unknown>).region === "string",
    )
  );
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
      path: "/api/owner/geofence-policy",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgId = request.nextUrl.searchParams.get("orgId");
  if (!orgId) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/geofence-policy",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: `org '${orgId}' not found` }, { status: 404 });
  }

  const policyResult = await getGeofencePolicy(orgId);
  if (!policyResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/owner/geofence-policy?orgId=${orgId}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: policyResult.error }, { status: 502 });
  }

  const evaluateIp = request.nextUrl.searchParams.get("evaluateIp");
  if (!evaluateIp) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/owner/geofence-policy?orgId=${orgId}`,
      status: 200,
      requestId,
    });
    return NextResponse.json({ orgId, policy: policyResult.data });
  }

  const checkResult = await checkGeofenceAccess(orgId, evaluateIp, actor);
  if (!checkResult.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/owner/geofence-policy?orgId=${orgId}&evaluateIp=${evaluateIp}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: checkResult.error }, { status: 502 });
  }

  const evaluation = checkResult.data;
  if (evaluation.violation) {
    // A real violation was actually detected against a configured policy
    // -- durably logged here (awaited: this is the compliance evidence
    // the enforcement control exists to produce), distinguishing a
    // durably-flagged-but-allowed access from one this endpoint would
    // actually reject, per the org's own `enforcementMode`.
    await writeAuditLogEntryAwaited({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/owner/geofence-policy?orgId=${orgId}&evaluateIp=${evaluateIp}`,
      status: 200,
      requestId,
      geofenceAction: evaluation.allowed ? "access_flagged" : "access_rejected",
      ...(evaluation.resolvedRegion ? { geofenceResolvedRegion: evaluation.resolvedRegion } : {}),
      geofenceContractedRegions: evaluation.contractedRegions,
    });
  } else {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/owner/geofence-policy?orgId=${orgId}&evaluateIp=${evaluateIp}`,
      status: 200,
      requestId,
    });
  }

  return NextResponse.json({ orgId, policy: policyResult.data, evaluation });
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
      path: "/api/owner/geofence-policy",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const orgId = typeof v?.orgId === "string" ? v.orgId : "";
  const contractedRegions = Array.isArray(v?.contractedRegions)
    ? (v.contractedRegions as unknown[]).filter((r): r is string => typeof r === "string")
    : null;
  const cidrRegionMap = v?.cidrRegionMap;
  const enforcementMode = v?.enforcementMode;

  if (
    !orgId ||
    !contractedRegions ||
    contractedRegions.length === 0 ||
    !isCidrRegionArray(cidrRegionMap) ||
    !isEnforcementMode(enforcementMode)
  ) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/geofence-policy",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "orgId, contractedRegions (non-empty string[]), cidrRegionMap ({cidr,region}[]), " +
          "and enforcementMode ('flag'|'reject') are required",
      },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/geofence-policy",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `org '${orgId}' not found` }, { status: 404 });
  }

  const result = await setGeofencePolicy({
    orgId,
    contractedRegions,
    cidrRegionMap,
    enforcementMode,
    updatedBy: actor,
  });

  const status = result.ok ? 200 : 502;
  await writeAuditLogEntryAwaited({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: "/api/owner/geofence-policy",
    status,
    requestId,
    ...(result.ok
      ? { geofenceAction: "policy_set" as const, geofenceContractedRegions: result.data.contractedRegions }
      : {}),
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ policy: result.data });
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
      path: "/api/owner/geofence-policy",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const orgId = typeof v?.orgId === "string" ? v.orgId : "";
  const identifierOrCidr = typeof v?.identifierOrCidr === "string" ? v.identifierOrCidr.trim() : "";
  const reason = typeof v?.reason === "string" ? v.reason.trim() : "";
  const ttlHours = typeof v?.ttlHours === "number" && v.ttlHours > 0 && v.ttlHours <= 168 ? v.ttlHours : null;

  if (!orgId || !identifierOrCidr || !reason || ttlHours === null) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/geofence-policy",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "orgId, identifierOrCidr, reason, and ttlHours (0 < ttlHours <= 168) are required",
      },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/geofence-policy",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `org '${orgId}' not found` }, { status: 404 });
  }

  const policyResult = await getGeofencePolicy(orgId);
  if (!policyResult.ok) {
    return NextResponse.json({ error: policyResult.error }, { status: 502 });
  }
  if (!policyResult.data) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/geofence-policy",
      status: 409,
      requestId,
    });
    return NextResponse.json(
      { error: `org '${orgId}' has no geofence policy configured -- PUT one first` },
      { status: 409 },
    );
  }

  const approval = await requireApproval({
    action: "geofence.exception.grant",
    targetId: orgId,
    requestedBy: actor,
    resourcePayload: {
      requestedGeofenceException: { identifierOrCidr, reason, ttlHours },
    },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/geofence-policy",
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
      path: "/api/owner/geofence-policy",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "geofence.exception.grant requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize this ` +
          "exception, then retry POST with the same orgId, identifierOrCidr, reason, and ttlHours.",
      },
      { status: 202 },
    );
  }

  const approved = approval.approval.resourcePayload?.requestedGeofenceException ?? {
    identifierOrCidr,
    reason,
    ttlHours,
  };

  const result = await applyGeofenceException({
    orgId,
    identifierOrCidr: approved.identifierOrCidr,
    reason: approved.reason,
    ttlHours: approved.ttlHours,
    grantedBy: actor,
  });

  const status = result.ok ? 200 : 502;
  await writeAuditLogEntryAwaited({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/owner/geofence-policy",
    status,
    requestId,
    ...(result.ok ? { geofenceAction: "exception_granted" as const } : {}),
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  return NextResponse.json({
    applied: true,
    exception: result.data,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}

