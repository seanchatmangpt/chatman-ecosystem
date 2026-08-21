import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { requireApproval } from "@/lib/approval-workflow";
import { getOrg } from "@/lib/orgs";
import {
  getScreeningRegister,
  isOrgClearedForScreening,
  runAndRecordScreening,
  recordScreeningOverride,
  type ContactRole,
} from "@/lib/denied-party-screening";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, writeAuditLogEntryAwaited } from "@/lib/audit-db";

// Real Denied-Party / Export-Control Screening Register endpoint
// (lib/denied-party-screening.ts) -- the hard procurement gate a
// Fortune-5 cross-border SaaS deal cannot close without: every org
// admin, billing contact, and named technical contact screened by name
// against this platform's own maintained denied-party list, with a
// queryable, timestamped, per-org register legal/export-compliance can
// review before signing off.
//
// Auth model, same org-scoped requireRoleIn boundary
// app/api/orgs/[id]/cmek/route.ts already establishes:
//   - GET: any authenticated member of THIS org (viewer and up) -- the
//     register and its computed "cleared" readout is not itself a
//     privileged action; a security reviewer or the org's own operators
//     routinely need to see it before a contract closes.
//   - POST: owner of THIS org -- runs a real screening for one named
//     contact and appends the result. Never itself gated behind
//     maker-checker (screening is read-only evidence-gathering against
//     the maintained list, the same "logging is not itself the
//     sensitive action" split lib/le-requests.ts's own header comment
//     documents for its ingest path); only a "potential_match" RESULT
//     then requires a second approver before the org is cleared.
//   - PUT: owner of THIS org, gated behind the SAME maker-checker
//     `denied-party.override` approval workflow
//     (lib/approval-workflow.ts's requireApproval)
//     `le-request.respond`/`subprocessor.registry.update` already use --
//     one owner's own say-so that a "potential_match" was a false
//     positive is never sufficient by itself; a second, distinct
//     owner-role approver must sign off before the override is recorded.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const CONTACT_ROLES = ["org_admin", "billing_contact", "technical_contact"] as const;
function isContactRole(value: unknown): value is ContactRole {
  return typeof value === "string" && (CONTACT_ROLES as readonly string[]).includes(value);
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const [registerResult, clearedResult] = await Promise.all([
    getScreeningRegister(orgId),
    isOrgClearedForScreening(orgId),
  ]);

  const status = registerResult.ok && clearedResult.ok ? 200 : 502;
  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/owner/${orgId}/denied-party-screening`,
    status,
    requestId,
  });

  if (!registerResult.ok) {
    return NextResponse.json({ error: registerResult.error }, { status: 502 });
  }
  if (!clearedResult.ok) {
    return NextResponse.json({ error: clearedResult.error }, { status: 502 });
  }

  return NextResponse.json({
    orgId,
    records: registerResult.data,
    cleared: clearedResult.data,
  });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const contactRole = v?.contactRole;
  const contactName = typeof v?.contactName === "string" ? v.contactName.trim() : "";
  const contactEmail = typeof v?.contactEmail === "string" ? v.contactEmail.trim() : "";

  if (!isContactRole(contactRole) || !contactName || !contactEmail) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "contactRole ('org_admin'|'billing_contact'|'technical_contact'), contactName, and contactEmail are required",
      },
      { status: 400 },
    );
  }

  const result = await runAndRecordScreening({
    orgId,
    contactRole,
    contactName,
    contactEmail,
    screenedByIdentifier: actor,
  });

  const status = result.ok ? 200 : 502;
  await writeAuditLogEntryAwaited({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/owner/${orgId}/denied-party-screening`,
    status,
    requestId,
    ...(result.ok
      ? {
          screeningAction: "screened" as const,
          screeningRecordId: result.data.id,
          screeningResult: result.data.result,
          screeningContactRole: contactRole,
        }
      : {}),
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ record: result.data });
}

const OVERRIDE_DECISIONS = ["cleared_to_proceed", "confirmed_blocked"] as const;
type OverrideDecision = (typeof OVERRIDE_DECISIONS)[number];
function isOverrideDecision(value: unknown): value is OverrideDecision {
  return typeof value === "string" && (OVERRIDE_DECISIONS as readonly string[]).includes(value);
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const access = await requireRoleIn(session, orgResult.data.namespace, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const screeningRecordId = typeof v?.screeningRecordId === "string" ? v.screeningRecordId : "";
  const decision = v?.decision;
  const justification = typeof v?.justification === "string" ? v.justification.trim() : "";

  if (!screeningRecordId || !isOverrideDecision(decision) || !justification) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "screeningRecordId, decision ('cleared_to_proceed'|'confirmed_blocked'), and justification are required",
      },
      { status: 400 },
    );
  }

  const register = await getScreeningRegister(orgId);
  if (!register.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: register.error }, { status: 502 });
  }
  const target = register.data.find((r) => r.id === screeningRecordId);
  if (!target) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: 404,
      requestId,
    });
    return NextResponse.json(
      { error: `no screening record found with id '${screeningRecordId}' for org '${orgId}'` },
      { status: 404 },
    );
  }

  const approval = await requireApproval({
    action: "denied-party.override",
    targetId: screeningRecordId,
    requestedBy: actor,
    resourcePayload: {
      requestedScreeningOverride: {
        orgId,
        contactRole: target.contactRole,
        contactName: target.contactName,
        contactEmail: target.contactEmail,
        matches: target.matches,
        decision,
        justification,
      },
    },
  });

  if ("error" in approval) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/owner/${orgId}/denied-party-screening`,
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
      method: "PUT",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: 202,
      requestId,
    });
    return NextResponse.json(
      {
        status: "pending_approval",
        approval: approval.request,
        message:
          "denied-party.override requires a second, distinct owner-role approver -- POST " +
          `/api/approvals/${approval.request.requestId} {decision:'approved'} to authorize recording ` +
          "this override, then retry PUT with the same screeningRecordId, decision, and justification.",
      },
      { status: 202 },
    );
  }

  const approved = approval.approval.resourcePayload?.requestedScreeningOverride ?? {
    orgId,
    contactRole: target.contactRole,
    contactName: target.contactName,
    contactEmail: target.contactEmail,
    matches: target.matches,
    decision,
    justification,
  };

  const result = await recordScreeningOverride({
    orgId,
    screeningRecordId,
    decision: approved.decision,
    decidedByIdentifier: actor,
    justification: approved.justification,
  });

  if (!result.ok) {
    const respStatus =
      result.error === "not_found"
        ? 404
        : result.error === "not_a_match" || result.error === "already_decided" || result.error === "self_override"
          ? 409
          : 502;
    await writeAuditLogEntryAwaited({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "PUT",
      path: `/api/owner/${orgId}/denied-party-screening`,
      status: respStatus,
      requestId,
      screeningRecordId,
    });
    return NextResponse.json({ error: result.error }, { status: respStatus });
  }

  await writeAuditLogEntryAwaited({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "PUT",
    path: `/api/owner/${orgId}/denied-party-screening`,
    status: 200,
    requestId,
    screeningAction: "override_recorded",
    screeningRecordId,
    screeningContactRole: target.contactRole,
  });

  return NextResponse.json({
    applied: true,
    record: result.data,
    requiredApproval: true,
    approvedBy: approval.approval.approvedBy,
  });
}
