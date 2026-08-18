import { NextRequest, NextResponse } from "next/server";
import { SESSION_COOKIE_NAME, verifySessionToken, type SessionPayload } from "@/lib/session";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { requireRole } from "@/lib/authz";
import {
  IMAGES_TO_SCAN,
  createVulnScanJob,
  deleteVulnScanJob,
  getVulnScanRun,
  newVulnScanJobName,
  syncVulnDenylist,
} from "@/lib/vuln-scan";

// Owner-only, both verbs -- Container Vulnerability Scanning creates a real
// k8s Job with a hostPath mount onto the node's own containerd socket, the
// same "most sensitive capability" class as Container Exec and Canary
// Deploy, so it gets the same "owner" floor, enforced here (the only real
// enforcement boundary -- this page's own client-side gate is UX only).
//
// POST starts a real scan run (creates the Job, returns immediately with
// its name and the fixed image list -- scanning genuinely takes tens of
// seconds across 7 images, so this is deliberately async: the client polls
// GET, never a single long-blocking request that risks the mesh's default
// route timeout).
// GET polls one run's real current status -- job completion counts plus,
// for every pod that has already terminated, its real parsed findings.
// DELETE tears down a finished run's Job (and, transitively, its pods).

async function requireSession(request: NextRequest): Promise<SessionPayload | null> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  return token ? await verifySessionToken(token) : null;
}

export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "POST",
      path: "/api/security-scan",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const jobName = newVulnScanJobName();
  const result = await createVulnScanJob(jobName);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "POST",
    path: "/api/security-scan",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({
    jobName,
    images: IMAGES_TO_SCAN.map((t) => ({ id: t.id, label: t.label, source: t.source, isControl: t.isControl })),
  });
}

export async function GET(request: NextRequest) {
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const access = await requireRole(session, "owner");
  if (!access.ok) return access.response!;

  const jobName = request.nextUrl.searchParams.get("jobName") ?? "";
  if (!jobName) {
    return NextResponse.json({ error: "jobName query param is required" }, { status: 400 });
  }

  const result = await getVulnScanRun(jobName);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }

  // Once the run is genuinely complete, push its real result into the
  // real admission-gate ConfigMap (lib/vuln-scan.ts's syncVulnDenylist)
  // so the cluster-side ValidatingAdmissionPolicy
  // (platform-deployments-block-critical-cves) reflects this scan on its
  // very next Deployment admission -- the actual hard-gate effect, not
  // just a UI report. A sync failure here does not fail the GET (the scan
  // result itself is still real and worth returning); it surfaces as
  // `denylistSyncError` for the panel to show honestly instead of
  // silently claiming the gate updated when it didn't.
  let denylist: { pattern: string; blockedRefs: string[] } | null = null;
  let denylistSyncError: string | null = null;
  if (result.data.complete) {
    const sync = await syncVulnDenylist(result.data);
    if (sync.ok) {
      denylist = sync.data;
    } else {
      denylistSyncError = sync.error;
    }
  }

  return NextResponse.json({ run: result.data, denylist, denylistSyncError });
}

export async function DELETE(request: NextRequest) {
  const requestId = newRequestId();
  const session = await requireSession(request);
  if (!session) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const actor = session.sub;

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor,
      method: "DELETE",
      path: "/api/security-scan",
      status: 403,
      requestId,
    });
    return access.response!;
  }

  const jobName = request.nextUrl.searchParams.get("jobName") ?? "";
  if (!jobName) {
    return NextResponse.json({ error: "jobName query param is required" }, { status: 400 });
  }

  const result = await deleteVulnScanJob(jobName);

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor,
    method: "DELETE",
    path: "/api/security-scan",
    status: result.ok ? 200 : 502,
    requestId,
  });

  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 502 });
  }
  return NextResponse.json({ ok: true });
}
