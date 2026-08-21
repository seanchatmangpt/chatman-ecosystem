import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntryAwaited } from "@/lib/audit-db";
import { logLeRequest, listLeRequests, type LeRequestType } from "@/lib/le-requests";

// Real, unattended intake endpoint for the Law-Enforcement / Government
// Data Request register (transparency log) -- see lib/le-requests.ts's
// own header comment for the full "logging receipt is deliberately not
// the sensitive action" rationale. Authenticated the SAME shared-secret-
// header pattern every other unattended app/api/internal/* route in this
// tree uses (see app/api/internal/fault-scan-snapshot/route.ts's own
// header comment for the one-time operator provisioning step:
// `kubectl create secret generic platform-le-requests-ingest-secret
// --from-literal=secret=...` in the `platform-console` namespace, then
// setting the matching `LE_REQUESTS_INGEST_SECRET` env on the console's
// own Deployment). Checked BEFORE anything else, since the caller here
// is the legal/privacy team's own intake tooling -- never a browser
// session -- and a missing configured secret fails closed (no bypass),
// same discipline every other cron/ingest route in this tree already
// establishes.
//
// GET is intentionally NOT exposed here: the shared-secret intake path
// is write-only (log a new request), matching the "ingest vs. act" split
// this module's own header comment documents -- reading the register
// back (with full per-request detail) is a session-authed, role-gated
// concern, see GET /api/owner/le-requests.
function isIngestAuthenticated(request: NextRequest): boolean {
  const expected = process.env.LE_REQUESTS_INGEST_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no ingest bypass, ever
  const presented = request.headers.get("x-le-requests-ingest-secret");
  return presented === expected;
}

const VALID_TYPES: LeRequestType[] = [
  "subpoena",
  "warrant",
  "court_order",
  "national_security_letter",
  "other",
];

function isLeRequestType(value: unknown): value is LeRequestType {
  return typeof value === "string" && (VALID_TYPES as string[]).includes(value);
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  if (!isIngestAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const body = await request.json().catch(() => null);
  const v = body as Record<string, unknown> | null;
  const requestType = v?.requestType;
  const requestingAuthority = typeof v?.requestingAuthority === "string" ? v.requestingAuthority.trim() : "";
  const jurisdiction = typeof v?.jurisdiction === "string" ? v.jurisdiction.trim() : "";
  const summary = typeof v?.summary === "string" ? v.summary.trim() : "";
  const referenceNumber = typeof v?.referenceNumber === "string" ? v.referenceNumber.trim() : undefined;
  const orgId = typeof v?.orgId === "string" ? v.orgId.trim() : undefined;
  const loggedBy = typeof v?.loggedBy === "string" ? v.loggedBy.trim() : "";

  if (!isLeRequestType(requestType) || !requestingAuthority || !jurisdiction || !summary || !loggedBy) {
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor: "le-requests-ingest",
      method: "POST",
      path: "/api/internal/le-requests",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      {
        error:
          "requestType ('subpoena'|'warrant'|'court_order'|'national_security_letter'|'other'), " +
          "requestingAuthority, jurisdiction, summary, and loggedBy are required " +
          "(referenceNumber and orgId are optional)",
      },
      { status: 400 },
    );
  }

  const result = await logLeRequest({
    requestType,
    requestingAuthority,
    jurisdiction,
    summary,
    loggedBy,
    ...(referenceNumber ? { referenceNumber } : {}),
    ...(orgId ? { orgId } : {}),
  });

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor: "le-requests-ingest",
    ...(orgId ? { orgId } : {}),
    method: "POST",
    path: "/api/internal/le-requests",
    status: result.ok ? 201 : 502,
    requestId,
    leRequestAction: "logged",
    ...(result.ok ? { leRequestId: result.data.requestId } : {}),
    leRequestType: requestType,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ request: result.data }, { status: 201 });
}

// Diagnostic/reconciliation read for the SAME intake tooling that just
// wrote a row -- e.g. confirming a just-logged request actually landed --
// gated behind the identical shared secret, never a session. Full
// per-request detail (never redacted here, unlike the public trust-page
// rollup) is appropriate because the caller already holds the shared
// ingest secret, the same trust boundary this route's own POST grants
// write access under.
export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  if (!isIngestAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const orgId = request.headers.get("x-le-requests-org") ?? undefined;
  const result = await listLeRequests(orgId);

  await writeAuditLogEntryAwaited({
    timestamp: new Date().toISOString(),
    actor: "le-requests-ingest",
    ...(orgId ? { orgId } : {}),
    method: "GET",
    path: "/api/internal/le-requests",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ requests: result.data });
}
