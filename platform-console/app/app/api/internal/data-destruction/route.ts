import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntryAwaited } from "@/lib/audit-db";
import { getOrg } from "@/lib/orgs";
import { verifyDataDestruction } from "@/lib/data-destruction-certificate";

// Real, unattended teardown-confirmation endpoint for the Certificate of
// Data Destruction capability -- see lib/data-destruction-certificate.ts's
// own header comment for what this can and cannot truthfully attest.
// Authenticated the SAME shared-secret-header pattern every other
// unattended app/api/internal/* route in this tree uses (see
// app/api/internal/fault-scan-snapshot/route.ts's own header comment for
// the one-time operator provisioning step: `kubectl create secret generic
// platform-data-destruction-verify-secret --from-literal=secret=...` in
// the `platform-console` namespace, then setting the matching
// `DATA_DESTRUCTION_VERIFY_SECRET` env on the console's own Deployment).
// Checked BEFORE anything else -- the caller here is offboarding/legal
// ops tooling reconciling a queued contract termination, never a browser
// session -- and a missing configured secret fails closed (no bypass),
// same discipline every other cron/ingest route in this tree already
// establishes.
//
// GET only: this route PERFORMS the real, live k8sRequest-backed
// verification (`verifyDataDestruction` -- real PVC list, real backup
// record scan) and reports it back; it never mints a certificate itself.
// Minting is a session-authed, maker-checker-gated act -- see POST
// /api/owner/data-destruction.
function isVerifyAuthenticated(request: NextRequest): boolean {
  const expected = process.env.DATA_DESTRUCTION_VERIFY_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no verify bypass, ever
  const presented = request.headers.get("x-data-destruction-verify-secret");
  return presented === expected;
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  if (!isVerifyAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const orgId = request.nextUrl.searchParams.get("orgId")?.trim();
  if (!orgId) {
    await writeAuditLogEntryAwaited({
      timestamp: new Date().toISOString(),
      actor: "data-destruction-verify",
      method: "GET",
      path: "/api/internal/data-destruction",
      status: 400,
      requestId,
    });
    return NextResponse.json({ error: "orgId query parameter is required" }, { status: 400 });
  }

  const orgResult = await getOrg(orgId);
  if (!orgResult.ok) {
    await writeAuditLogEntryAwaited({
      orgId,
      timestamp: new Date().toISOString(),
      actor: "data-destruction-verify",
      method: "GET",
      path: "/api/internal/data-destruction",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgResult.error }, { status: 502 });
  }
  if (!orgResult.data) {
    await writeAuditLogEntryAwaited({
      orgId,
      timestamp: new Date().toISOString(),
      actor: "data-destruction-verify",
      method: "GET",
      path: "/api/internal/data-destruction",
      status: 404,
      requestId,
    });
    return NextResponse.json({ error: "org not found" }, { status: 404 });
  }

  const result = await verifyDataDestruction(orgId, orgResult.data.namespace);

  await writeAuditLogEntryAwaited({
    orgId,
    timestamp: new Date().toISOString(),
    actor: "data-destruction-verify",
    method: "GET",
    path: "/api/internal/data-destruction",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ verification: result.data });
}
