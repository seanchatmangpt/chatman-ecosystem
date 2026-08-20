import { NextRequest, NextResponse } from "next/server";
import {
  newRequestId,
  queryAuditLogSince,
  resolveAuditExportToken,
  verifyAuditChain,
  writeAuditLogEntry,
} from "@/lib/audit-db";

// Real, external-facing, schema-versioned SIEM export contract -- the
// documented endpoint a customer's Splunk/Datadog/Sentinel forwarder
// commits its connector build against, distinct from GET /api/audit (the
// internal, session-gated admin-UI query surface a Fortune-5 security
// team will not build unattended automation on top of). Full field-by-
// field stability guarantees: docs/AUDIT-EXPORT-SCHEMA.md.
//
// Auth: a per-org, owner-issued `Authorization: Bearer aet_live_...`
// export token (lib/audit-db.ts's createAuditExportToken /
// resolveAuditExportToken), never the session cookie and never a
// general-purpose pk_live_ API key -- a SIEM forwarder authenticates
// unattended, on a schedule, forever, with a credential scoped to nothing
// but `audit:read` and independently revocable. middleware.ts exempts
// this exact path from its cookie-or-pk_live_ gate (AUDIT_EXPORT_PATTERN)
// so the request reaches this handler's own check.
//
// Cursor pagination: `since` is an opaque cursor (a value this endpoint
// itself returned as `next_cursor` on a prior call, or a bare RFC3339
// timestamp for a forwarder's first poll) -- real keyset pagination via
// lib/audit-db.ts's queryAuditLogSince (`ORDER BY ts ASC, id ASC`,
// `WHERE (ts, id) > cursor`), never OFFSET, so polling never skips or
// repeats a row under concurrent writes to the underlying audit_log
// table. `limit` defaults to 500, capped at 2000 -- the same "small,
// safe default, generous but bounded ceiling" shape as every other
// paginated endpoint in this console (see /api/audit's DEFAULT_LIMIT/
// MAX_LIMIT).
//
// `schema_version` is frozen as the literal `"1"` -- see
// docs/AUDIT-EXPORT-SCHEMA.md for what "frozen" guarantees (additive-only
// field changes bump nothing; any breaking change ships as `"2"` on a
// distinct, versioned response shape, never a silent mutation of `"1"`'s
// contract).
//
// Runs on the Node.js runtime (default for route handlers) -- lib/k8s.ts
// and the `pg` driver lib/audit-db.ts uses both need it.

const SCHEMA_VERSION = "1" as const;

const DEFAULT_LIMIT = 500;
const MAX_LIMIT = 2000;

export async function GET(request: NextRequest) {
  const requestId = newRequestId();

  const authHeader = request.headers.get("authorization");
  const presentedToken = authHeader?.startsWith("Bearer ")
    ? authHeader.slice("Bearer ".length).trim()
    : null;

  if (!presentedToken) {
    return NextResponse.json(
      { error: "unauthenticated", reason: "Authorization: Bearer <audit export token> is required" },
      { status: 401 },
    );
  }

  const resolved = await resolveAuditExportToken(presentedToken);
  if (!resolved) {
    return NextResponse.json(
      { error: "unauthenticated", reason: "audit export token is invalid, unknown, or revoked" },
      { status: 401 },
    );
  }

  const params = request.nextUrl.searchParams;
  const since = params.get("since")?.trim() || undefined;

  const limitParam = Number(params.get("limit"));
  const limit =
    Number.isFinite(limitParam) && limitParam > 0
      ? Math.min(Math.floor(limitParam), MAX_LIMIT)
      : DEFAULT_LIMIT;

  const [queryResult, chainResult] = await Promise.all([
    queryAuditLogSince(since, limit, resolved.orgId),
    verifyAuditChain(),
  ]);

  // Every export call is itself logged -- export activity against
  // customer audit data is exactly the kind of action this trail exists
  // to capture, same "the control that reads sensitive data is itself
  // audited" discipline GET /api/audit/verify already applies. Actor is
  // the resolved org id (this credential has no human session identity
  // behind it), distinguishable in the trail from a session-cookie or
  // pk_live_-key actor string by its own recognizable shape.
  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: `audit-export-token:${resolved.orgId}`,
    method: "GET",
    path: "/api/v1/audit-export",
    status: queryResult.ok ? 200 : 502,
    requestId,
    orgId: resolved.orgId,
  });

  if (!queryResult.ok) {
    return NextResponse.json({ error: queryResult.error }, { status: 502 });
  }

  return NextResponse.json({
    schema_version: SCHEMA_VERSION,
    events: queryResult.data.rows,
    next_cursor: queryResult.data.nextCursor ?? null,
    chain_verified: chainResult.ok ? chainResult.data.valid : false,
  });
}
