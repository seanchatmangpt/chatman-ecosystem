import { NextRequest, NextResponse } from "next/server";
import { roleIdentifierFor, requireRole } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import {
  applySubprocessorChange,
  listSubprocessors,
  type SubprocessorCategory,
  type SubprocessorRecord,
} from "@/lib/subprocessors";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";

// Real, platform-wide Sub-processor Registry endpoints -- see
// lib/subprocessors.ts's header comment for the full compliance
// rationale (the GDPR Art. 28(2) "list of sub-processors" gap upstream
// of lib/dpa-records.ts and lib/data-residency-attestation.ts) and the
// maker-checker + change-notification design.
//
// Auth model, same "app-level RBAC on top of the console's own
// ServiceAccount RBAC" boundary as every other route in this tree:
//   - GET: any authenticated session (member and up) -- reading the
//     registry is not itself a privileged action; a customer's own
//     legal/procurement contact routinely needs to see it.
//   - POST: platform "owner" (lib/authz.ts's requireRole), gated behind
//     the SAME maker-checker `subprocessor.registry.update` approval
//     workflow (lib/approval-workflow.ts's requireApproval)
//     `pricing.override`/`sso.role-mapping.update` already use -- one
//     owner's own say-so is never sufficient by itself to add a new
//     sub-processor and fan out a change-notice to every customer org.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

function isCategory(value: unknown): value is SubprocessorCategory {
  return value === "cloud-infrastructure" || value === "third-party-service";
}

function parseRecord(body: unknown): SubprocessorRecord | null {
  const v = body as Record<string, unknown> | null;
  if (!v) return null;
  const id = typeof v.id === "string" ? v.id.trim() : "";
  const name = typeof v.name === "string" ? v.name.trim() : "";
  const category = v.category;
  const regions = Array.isArray(v.regions) ? v.regions.filter((r) => typeof r === "string") : [];
  const purpose = typeof v.purpose === "string" ? v.purpose.trim() : "";
  const dataCategories = Array.isArray(v.dataCategories)
    ? v.dataCategories.filter((d) => typeof d === "string")
    : [];
  if (!id || !/^[-._a-zA-Z0-9]+$/.test(id)) return null;
  if (!name || !isCategory(category) || !purpose) return null;
  return { id, name, category, regions, purpose, dataCategories };
}

export async function GET(request: NextRequest) {
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
      path: "/api/subprocessors",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listSubprocessors();
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/subprocessors",
    status: result.ok ? 200 : 502,
    requestId,
  });
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ subprocessors: result.data });
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
      path: "/api/subprocessors",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const record = parseRecord(body);
  if (!record) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/subprocessors",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "id (ConfigMap-key-safe), name, category ('cloud-infrastructure'|'third-party-service'), " +
          "and purpose are required; regions/dataCategories must be string arrays if provided",
      },
      { status: 400 },
    );
  }

  const approval = await requireApproval({
    action: "subprocessor.registry.update",
    targetId: record.id,
    requestedBy: actor,
    resourcePayload: { requestedSubprocessorChange: { action: "added", record } },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/subprocessors",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: approval.error }, { status: 502 });
  }

  if (!approval.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/subprocessors",
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "subprocessor.registry.update requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize adding ` +
          "this sub-processor, then retry POST.",
      },
      { status: 202 },
    );
  }

  const approvedChange = approval.approval.resourcePayload?.requestedSubprocessorChange ?? {
    action: "added" as const,
    record,
  };
  const result = await applySubprocessorChange({
    action: approvedChange.action,
    record: approvedChange.record,
    changedByIdentifier: actor,
  });

  if (!result.ok) {
    const status = "error" in result && typeof result.error === "string" && result.error === "duplicate_id" ? 409 : 502;
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/subprocessors",
      status,
      requestId,
      subprocessorId: record.id,
    });
    return NextResponse.json({ error: result.error }, { status });
  }

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/subprocessors",
    status: 201,
    requestId,
    subprocessorAction: result.data.event.action,
    subprocessorId: result.data.event.record.id,
    subprocessorNotifiedOrgCount: result.data.notifiedOrgCount,
  });

  return NextResponse.json(
    {
      applied: true,
      event: result.data.event,
      notifiedOrgCount: result.data.notifiedOrgCount,
      requiredApproval: true,
      approvedBy: approval.approval.approvedBy,
    },
    { status: 201 },
  );
}
