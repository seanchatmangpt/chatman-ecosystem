import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { verifyHashChain } from "@/lib/audit-integrity";
import { requireRoleIn } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";

// Real, on-demand tamper-evidence ATTESTATION -- distinct from both
// GET /api/audit/export (raw NDJSON for SIEM ingestion, no verification
// claim attached) and GET /api/v1/audit-export (which inlines the
// platform-wide `chain_verified` boolean but never a per-row breakdown).
// A Fortune-5 SOC2/forensic-readiness reviewer asks "prove your audit log
// has not been tampered with" for a SPECIFIC org, over a SPECIFIC period
// -- this is the endpoint that answers exactly that question, with a
// computed result (verified / rowsChecked / firstBreakAt), not the raw
// chain for the auditor to re-derive themselves. See
// lib/audit-integrity.ts's header comment for why this is a genuinely
// different (narrower, org-scoped, per-row) check than
// lib/audit-db.ts's platform-wide verifyAuditChain, not a duplicate of it.
//
// Auth: session-gated, org-scoped owner role -- the exact same boundary
// GET /api/orgs/[id]/audit-export-tokens uses to gate minting the SIEM
// export credential for this same org (requireRoleIn against the org's
// own namespace-local platform-console-org-roles ConfigMap, resolved via
// lib/orgs.ts's getOrg). An owner of org A must never be able to pull an
// integrity attestation scoped to org B's audit trail.
//
// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// and the `pg` driver lib/audit-db.ts/lib/audit-integrity.ts use both
// need it.
// Results are NEVER persisted speculatively: every call re-derives the
// hash chain live against the current table (lib/audit-integrity.ts's
// verifyHashChain), so the report is always current rather than a cached
// answer that could go stale the moment a new row lands.

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();

  const params = request.nextUrl.searchParams;
  const orgId = params.get("orgId")?.trim();
  const from = params.get("from")?.trim() || undefined;
  const to = params.get("to")?.trim() || undefined;

  if (!orgId) {
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  // Real validation, matching GET /api/audit/export's own up-front check:
  // reject an un-parseable from/to with a real 400 rather than letting it
  // fail deep inside the SQL layer.
  for (const [label, value] of [["from", from] as const, ["to", to] as const]) {
    if (value !== undefined && Number.isNaN(Date.parse(value))) {
      return NextResponse.json({ error: `invalid ${label}: not a parseable date` }, { status: 400 });
    }
  }

  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

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
      method: "GET",
      path: "/api/audit/integrity-report",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const result = await verifyHashChain(orgId, from, to);

  writeAuditLogEntry({
    orgId,
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path: `/api/audit/integrity-report (${orgId}${from ? `, from=${from}` : ""}${to ? `, to=${to}` : ""})`,
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  return NextResponse.json({
    orgId,
    from: from ?? null,
    to: to ?? null,
    verified: result.data.verified,
    rowsChecked: result.data.rowsChecked,
    firstBreakAt: result.data.firstBreakAt,
    generatedAt: new Date().toISOString(),
  });
}
