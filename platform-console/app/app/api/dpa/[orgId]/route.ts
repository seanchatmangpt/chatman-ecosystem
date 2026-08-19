import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { appendDpaRecord, getDpaHistory, hashDpaDocumentText, type DpaRecord } from "@/lib/dpa-records";

// Real per-org Data Processing Agreement e-signature RECORD store --
// see lib/dpa-records.ts's header comment for the full rationale and the
// append-only-array-in-one-ConfigMap-value pattern this reuses from
// lib/audit-db.ts's own hash-chain segments. This route never performs
// e-signing; `signatureReference` only stores an external e-sign
// system's document ID/URL.
//
// GET is owner+member readable (a procurement/legal reviewer with plain
// member access needs to be able to confirm DPA status without an owner
// escalation); POST is owner-only, same boundary DELETE /api/orgs/[id]
// and PUT /api/orgs/[id]/branding already use -- recording a legally
// binding compliance artifact is at least as sensitive as any other
// owner-only write in this console.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}(T.*)?$/;

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

  const access = await requireRoleIn(session, orgResult.data.namespace, "member");
  if (!access.ok) {
    writeAuditLogEntry({
      orgId,
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: `/api/dpa/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const history = await getDpaHistory(orgId);
  if (!history.ok) {
    return NextResponse.json({ error: history.error }, { status: 502 });
  }

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/dpa/${orgId}`,
    status: 200,
    requestId,
  });

  return NextResponse.json(history.data);
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
      path: `/api/dpa/${orgId}`,
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const body = await request.json().catch(() => null);
  const version = typeof body?.version === "string" ? body.version.trim() : "";
  const effectiveDate = typeof body?.effectiveDate === "string" ? body.effectiveDate.trim() : "";
  const signerName = typeof body?.signerName === "string" ? body.signerName.trim() : "";
  const signerEmail = typeof body?.signerEmail === "string" ? body.signerEmail.trim() : "";
  const signatureReference =
    typeof body?.signatureReference === "string" ? body.signatureReference.trim() : "";
  // Either the caller already computed the sha256 digest (documentHash)
  // itself, or pastes the actual signed text (documentText) and this
  // route hashes it -- never both required, but at least one.
  const documentHash = typeof body?.documentHash === "string" ? body.documentHash.trim() : "";
  const documentText = typeof body?.documentText === "string" ? body.documentText : "";

  if (!version) {
    return NextResponse.json({ error: "version is required" }, { status: 400 });
  }
  if (!effectiveDate || !DATE_RE.test(effectiveDate)) {
    return NextResponse.json(
      { error: "effectiveDate is required and must be an ISO 8601 date" },
      { status: 400 },
    );
  }
  if (!signerName) {
    return NextResponse.json({ error: "signerName is required" }, { status: 400 });
  }
  if (!signerEmail || !EMAIL_RE.test(signerEmail)) {
    return NextResponse.json(
      { error: "signerEmail is required and must be a valid email" },
      { status: 400 },
    );
  }
  if (!signatureReference) {
    return NextResponse.json({ error: "signatureReference is required" }, { status: 400 });
  }
  const resolvedDocumentHash = documentHash || (documentText ? hashDpaDocumentText(documentText) : "");
  if (!resolvedDocumentHash) {
    return NextResponse.json(
      { error: "either documentHash or documentText is required" },
      { status: 400 },
    );
  }

  const priorHistory = await getDpaHistory(orgId);
  const wasSuperseding = priorHistory.ok && priorHistory.data.records.length > 0;

  const record: DpaRecord = {
    version,
    effectiveDate,
    signerName,
    signerEmail,
    signatureReference,
    documentHash: resolvedDocumentHash,
    recordedByIdentifier: actor,
    recordedAt: new Date().toISOString(),
  };

  const appended = await appendDpaRecord(orgId, record);
  if (!appended.ok) {
    return NextResponse.json({ error: appended.error }, { status: 502 });
  }

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/dpa/${orgId} (${wasSuperseding ? "dpa.superseded" : "dpa.recorded"}: version=${version}, signer=${signerEmail})`,
    status: 201,
    requestId,
  });

  return NextResponse.json(appended.data, { status: 201 });
}
