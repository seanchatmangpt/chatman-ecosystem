import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import {
  getLegalHold,
  listLegalHolds,
  placeLegalHold,
  releaseLegalHold,
  requireLegalHoldReleaseApproval,
  type LegalHoldScope,
} from "@/lib/legal-hold";

// Real, platform-owner-gated Legal Hold endpoint -- see
// lib/legal-hold.ts's own header comment for the full scope
// (storage/maker-checker asymmetry/enforcement). Same "platform owner,
// not merely an org-role owner" auth bar GET/PUT /api/owner/insurance-
// attestation and GET/PUT /api/owner/le-requests already set
// (lib/authz.ts's requireRole, not requireRoleIn) -- litigation holds
// are a platform-operations/legal fact, not something a customer org's
// own "owner" role can self-serve.
//
//   - GET: lists every recorded hold, optionally narrowed to the holds
//     that would restrict a given org (?orgId=...).
//   - POST: places a new, immediately-active hold -- never approval-gated
//     (a legal team member must always be able to stop scheduled
//     destruction alone; see lib/legal-hold.ts's header comment).
//   - PUT: releases an existing hold, gated behind the SAME
//     maker-checker `legal-hold.release` approval workflow
//     `dsar.erasure`/`dr.failover` already use -- one owner's own say-so
//     that litigation has concluded is never sufficient by itself.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isScope(value: unknown): value is LegalHoldScope {
  return value === "platform" || value === "org";
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
      path: "/api/owner/legal-hold",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const orgId = request.nextUrl.searchParams.get("orgId") ?? undefined;
  const result = await listLegalHolds(orgId);

  writeAuditLogEntry({
    ...(orgId ? { orgId } : {}),
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: orgId ? `/api/owner/legal-hold?orgId=${encodeURIComponent(orgId)}` : "/api/owner/legal-hold",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ holds: result.data });
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
      path: "/api/owner/legal-hold",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const b = body as Record<string, unknown> | null;

  const scope = b?.scope;
  const orgIdInput = typeof b?.orgId === "string" ? b.orgId.trim() : "";
  const name = typeof b?.name === "string" ? b.name.trim() : "";
  const reason = typeof b?.reason === "string" ? b.reason.trim() : "";

  if (!isScope(scope) || !name || !reason) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/legal-hold",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "scope ('platform'|'org'), name, and reason are all required" },
      { status: 400 },
    );
  }
  if (scope === "org" && !orgIdInput) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/owner/legal-hold",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "orgId is required when scope is 'org'" }, { status: 400 });
  }

  if (scope === "org") {
    const orgResult = await getOrg(orgIdInput);
    if (!orgResult.ok) {
      writeAuditLogEntry({
        orgId: orgIdInput,
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: "/api/owner/legal-hold",
        status: 502,
        requestId,
      });
      return NextResponse.json({ error: orgResult.error }, { status: 502 });
    }
    if (!orgResult.data) {
      writeAuditLogEntry({
        orgId: orgIdInput,
        timestamp: new Date().toISOString(),
        actor,
        method: "POST",
        path: "/api/owner/legal-hold",
        status: 404,
        requestId,
      });
      return NextResponse.json({ error: "org not found" }, { status: 404 });
    }
  }

  const result = await placeLegalHold({
    scope,
    orgId: scope === "org" ? orgIdInput : null,
    name,
    reason,
    createdBy: actor,
  });

  writeAuditLogEntry({
    ...(scope === "org" ? { orgId: orgIdInput } : {}),
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/owner/legal-hold",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ hold: result.data }, { status: 201 });
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
      path: "/api/owner/legal-hold",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const b = body as Record<string, unknown> | null;
  const holdId = typeof b?.holdId === "string" ? b.holdId.trim() : "";
  const releaseReason = typeof b?.releaseReason === "string" ? b.releaseReason.trim() : "";

  if (!holdId || !releaseReason) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/legal-hold",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "holdId and releaseReason are both required" }, { status: 400 });
  }

  const existing = await getLegalHold(holdId);
  if (!existing.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/legal-hold",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: existing.error }, { status: 502 });
  }
  if (!existing.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/legal-hold",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: `no legal hold found with id '${holdId}'` }, { status: 404 });
  }
  if (existing.data.status === "released") {
    writeAuditLogEntry({
      ...(existing.data.orgId ? { orgId: existing.data.orgId } : {}),
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/legal-hold",
      status: 200,
      requestId,
    });
    return NextResponse.json({ released: true, hold: existing.data });
  }

  const approval = await requireLegalHoldReleaseApproval({
    hold: existing.data,
    releaseReason,
    requestedBy: actor,
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      ...(existing.data.orgId ? { orgId: existing.data.orgId } : {}),
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/legal-hold",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      ...(existing.data.orgId ? { orgId: existing.data.orgId } : {}),
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/legal-hold",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "legal-hold.release requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize releasing this ` +
          "hold, then retry PUT.",
      },
      { status: 202 },
    );
  }

  const approvedRelease = approval.approval.resourcePayload?.requestedLegalHoldRelease;
  if (!approvedRelease) {
    writeAuditLogEntry({
      ...(existing.data.orgId ? { orgId: existing.data.orgId } : {}),
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: "/api/owner/legal-hold",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: "approved request is missing its release payload" }, { status: 502 });
  }

  const released = await releaseLegalHold({
    holdId: approvedRelease.holdId,
    releasedBy: approval.approval.approvedBy ?? actor,
    releaseReason: approvedRelease.releaseReason,
  });

  writeAuditLogEntry({
    ...(existing.data.orgId ? { orgId: existing.data.orgId } : {}),
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: "/api/owner/legal-hold",
    status: released.ok ? 200 : 502,
    requestId,
  });

  if (!released.ok) {
    return NextResponse.json({ error: released.error }, { status: 502 });
  }
  return NextResponse.json({ released: true, hold: released.data, approvedBy: approval.approval.approvedBy });
}
