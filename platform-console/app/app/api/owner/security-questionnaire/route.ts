import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole, roleIdentifierFor } from "@/lib/authz";
import {
  generateSecurityQuestionnaireBundle,
  listSecurityQuestionnaireExports,
  buildSecurityQuestionnaireArchive,
} from "@/lib/security-questionnaire-export";

// Real Security Questionnaire Evidence Bundle export (CAIQ/SIG-style,
// lib/security-questionnaire-export.ts) -- assembles the already-real
// SBOM/CVE-provenance, secret/certificate rotation compliance, data
// residency, SSO/SCIM role-mapping drift, and audit-log hash-chain
// integrity evidence this platform already produces into one downloadable
// ZIP a procurement/security reviewer can work from directly, instead of
// a manual back-and-forth over each control separately.
//
// Same owner-only floor as GET/POST /api/security-scan/sbom: every
// section this bundle assembles is itself owner-gated evidence (rotation
// compliance, residency, SSO drift, and audit integrity all read
// org-security-sensitive state), so gating the aggregate export any
// looser would let a non-owner obtain, in one call, evidence they could
// not have pulled from any one of the underlying routes themselves.
//
// GET lists every bundle ever generated (manifest only -- no archive
// bytes are persisted, see lib/security-questionnaire-export.ts's header
// comment). POST generates a fresh bundle from live/already-real evidence
// and streams the ZIP archive back directly in the same response --
// there is no separate signed-download-URL hop, since this route is
// already session-authed and owner-gated end to end.
//
// `orgId` (query string on GET filtering is not offered -- history is
// platform-wide by manifest; POST accepts `orgId` in the JSON body)
// scopes the four org-specific sections; omitting it produces a
// platform-wide bundle where only the SBOM section carries real evidence
// and the rest are honest, typed `available: false` gaps -- never
// fabricated org-scoped answers.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
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
    // org-agnostic: this lists a platform-wide history record with no
    // single-tenant org boundary, same allowlisted class as
    // GET /api/security-scan/sbom -- see scripts/check-audit-org-coverage.ts
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path: "/api/owner/security-questionnaire",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await listSecurityQuestionnaireExports();

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: "/api/owner/security-questionnaire",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ exports: result.data });
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
      path: "/api/owner/security-questionnaire",
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

  const result = await generateSecurityQuestionnaireBundle(orgId, actor);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: `/api/owner/security-questionnaire${orgId ? `?orgId=${encodeURIComponent(orgId)}` : ""}`,
    status: result.ok ? 200 : 400,
    requestId,
    ...(orgId ? { orgId } : {}),
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }

  const { archive, filename } = buildSecurityQuestionnaireArchive(result.data);

  return new NextResponse(new Uint8Array(archive), {
    status: 200,
    headers: {
      "content-type": "application/zip",
      "cache-control": "private, no-store",
      "content-disposition": `attachment; filename="${filename}"`,
      "x-security-questionnaire-export-id": result.data.manifest.id,
    },
  });
}
