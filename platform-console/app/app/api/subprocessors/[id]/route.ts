import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import {
  applySubprocessorChange,
  getSubprocessor,
  type SubprocessorCategory,
  type SubprocessorRecord,
} from "@/lib/subprocessors";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";

// GET one sub-processor's full history; PUT updates it; DELETE removes it
// -- both mutations gated behind the exact same
// `subprocessor.registry.update` maker-checker approval workflow
// POST /api/subprocessors uses. See lib/subprocessors.ts's header
// comment for the full design rationale.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isCategory(value: unknown): value is SubprocessorCategory {
  return value === "cloud-infrastructure" || value === "third-party-service";
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const access = await requireRole(session, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/subprocessors/${id}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await getSubprocessor(id);
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/subprocessors/${id}`,
    status: result.ok ? (result.data ? 200 : 404) : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  if (!result.data) {
    return NextResponse.json({ error: "sub-processor not found" }, { status: 404 });
  }
  return NextResponse.json({ subprocessor: result.data });
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
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
      path: `/api/subprocessors/${id}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const existing = await getSubprocessor(id);
  if (!existing.ok) {
    return NextResponse.json({ error: existing.error }, { status: 502 });
  }
  if (!existing.data || !existing.data.active) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/subprocessors/${id}`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "sub-processor not found or already removed" }, { status: 404 });
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const name = typeof v?.name === "string" ? v.name.trim() : existing.data.record!.name;
  const category = isCategory(v?.category) ? v!.category : existing.data.record!.category;
  const regions = Array.isArray(v?.regions)
    ? (v!.regions as unknown[]).filter((r): r is string => typeof r === "string")
    : existing.data.record!.regions;
  const purpose = typeof v?.purpose === "string" ? v.purpose.trim() : existing.data.record!.purpose;
  const dataCategories = Array.isArray(v?.dataCategories)
    ? (v!.dataCategories as unknown[]).filter((d): d is string => typeof d === "string")
    : existing.data.record!.dataCategories;

  if (!name || !purpose) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/subprocessors/${id}`,
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "name and purpose must be non-empty" }, { status: 400 });
  }

  const record: SubprocessorRecord = { id, name, category, regions, purpose, dataCategories };

  const approval = await requireApproval({
    action: "subprocessor.registry.update",
    targetId: id,
    requestedBy: actor,
    resourcePayload: { requestedSubprocessorChange: { action: "updated", record } },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/subprocessors/${id}`,
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
      path: `/api/subprocessors/${id}`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "subprocessor.registry.update requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize updating ` +
          "this sub-processor, then retry PUT.",
      },
      { status: 202 },
    );
  }

  const approvedChange = approval.approval.resourcePayload?.requestedSubprocessorChange ?? {
    action: "updated" as const,
    record,
  };
  const result = await applySubprocessorChange({
    action: approvedChange.action,
    record: approvedChange.record,
    changedByIdentifier: actor,
  });

  if (!result.ok) {
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/subprocessors/${id}`,
      status: 502,
      requestId,
      subprocessorId: id,
    });
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/subprocessors/${id}`,
    status: 200,
    requestId,
    subprocessorAction: result.data.event.action,
    subprocessorId: id,
    subprocessorNotifiedOrgCount: result.data.notifiedOrgCount,
  });

  return NextResponse.json({
    applied: true,
    event: result.data.event,
    notifiedOrgCount: result.data.notifiedOrgCount,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
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
      path: `/api/subprocessors/${id}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const existing = await getSubprocessor(id);
  if (!existing.ok) {
    return NextResponse.json({ error: existing.error }, { status: 502 });
  }
  if (!existing.data || !existing.data.active || !existing.data.record) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/subprocessors/${id}`,
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "sub-processor not found or already removed" }, { status: 404 });
  }

  const record = existing.data.record;

  const approval = await requireApproval({
    action: "subprocessor.registry.update",
    targetId: id,
    requestedBy: actor,
    resourcePayload: { requestedSubprocessorChange: { action: "removed", record } },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/subprocessors/${id}`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/subprocessors/${id}`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "subprocessor.registry.update requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize removing ` +
          "this sub-processor, then retry DELETE.",
      },
      { status: 202 },
    );
  }

  const approvedChange = approval.approval.resourcePayload?.requestedSubprocessorChange ?? {
    action: "removed" as const,
    record,
  };
  const result = await applySubprocessorChange({
    action: approvedChange.action,
    record: approvedChange.record,
    changedByIdentifier: actor,
  });

  if (!result.ok) {
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: `/api/subprocessors/${id}`,
      status: 502,
      requestId,
      subprocessorId: id,
    });
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: `/api/subprocessors/${id}`,
    status: 200,
    requestId,
    subprocessorAction: result.data.event.action,
    subprocessorId: id,
    subprocessorNotifiedOrgCount: result.data.notifiedOrgCount,
  });

  return NextResponse.json({
    applied: true,
    event: result.data.event,
    notifiedOrgCount: result.data.notifiedOrgCount,
    requiredApproval: true,
  });
}
