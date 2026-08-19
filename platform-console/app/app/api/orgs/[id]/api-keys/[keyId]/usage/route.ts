import { NextRequest, NextResponse } from "next/server";
import { requireRoleIn, roleIdentifierFor } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { newRequestId, writeAuditLogEntry, queryApiKeyUsage, isApiKeyUsageWindow } from "@/lib/audit-db";
import { getApiKeyById } from "@/lib/api-keys";

// Customer-facing API key usage analytics: closes the gap that
// lib/api-keys.ts already tracks pk_live_ keys and middleware.ts already
// writes one platform_console.audit_log row per authenticated request
// (now carrying that key's real keyId + org_id + duration_ms, see
// AuditLogEntry's doc comments in lib/audit-log.ts), but until this route
// nothing surfaced a per-key calls/latency/error-rate rollup to the
// customer -- the same "which of my keys is driving traffic, at what
// error rate, at what latency" view Stripe/Twilio/Datadog ship on their
// own API-key dashboards, and the natural lead-in to this console's
// already-built rate-limit-tier upsell (a customer has to SEE they're
// near a ceiling before they'll pay to raise it).
//
// GET-only, viewer-and-up gated against THIS org's own namespace-local
// `platform-console-org-roles` ConfigMap (lib/authz.ts's requireRoleIn) --
// same floor as app/api/orgs/[id]/branding/route.ts's GET: reading your
// own org's usage isn't a privileged write, but it must still be scoped
// to a real, authenticated member of this specific org, never any
// authenticated session platform-wide. `keyId` in the URL is resolved via
// lib/api-keys.ts's getApiKeyById to confirm it names a real, live key
// before ever querying its usage -- a 404 on an unknown id, not an empty
// (and misleadingly "zero calls") result.

async function requireSession(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; keyId: string }> },
) {
  const { id, keyId } = await params;
  const requestId = newRequestId();
  const path = `/api/orgs/${id}/api-keys/${keyId}/usage`;
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = roleIdentifierFor(session);

  const orgResult = await getOrg(id);
  if (!orgResult.ok) {
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  // Any authenticated member of this org (viewer and up) may read a
  // key's usage -- same floor as branding's GET, since this is a
  // read-only view of this org's own traffic, not a privileged action.
  const access = await requireRoleIn(session, orgResult.data.namespace, "viewer");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 403,
      requestId,
      orgId: id,
    });
    return access.response!;
  }

  const keyResult = await getApiKeyById(keyId);
  if (!keyResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 502,
      requestId,
      orgId: id,
    });
    return NextResponse.json({ error: keyResult.error }, { status: 502 });
  }
  if (!keyResult.data) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 404,
      requestId,
      orgId: id,
    });
    return NextResponse.json({ error: `no api key found with id '${keyId}'` }, { status: 404 });
  }

  const windowParam = request.nextUrl.searchParams.get("window") ?? "24h";
  if (!isApiKeyUsageWindow(windowParam)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "GET",
      path,
      status: 400,
      requestId,
      orgId: id,
    });
    return NextResponse.json(
      { error: "invalid 'window' -- must be one of '1h', '24h', '7d', '30d'" },
      { status: 400 },
    );
  }

  const usageResult = await queryApiKeyUsage(id, keyId, windowParam);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "GET",
    path,
    status: usageResult.ok ? 200 : 502,
    requestId,
    orgId: id,
  });

  if (!usageResult.ok) {
    return NextResponse.json({ error: usageResult.error }, { status: 502 });
  }
  return NextResponse.json({
    key: keyResult.data,
    usage: usageResult.data,
  });
}
