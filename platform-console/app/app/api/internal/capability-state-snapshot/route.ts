import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import { isSchedulableNamespace } from "@/lib/scheduled-jobs";
import {
  getCastleDeployment,
  listCastleJobs,
  ALLOWED_CASTLE_VERBS,
  type AllowedCastleVerbId,
  type CastleJob,
} from "@/lib/castle";
import { getActiveFreeze } from "@/lib/freeze-windows";
import { findApprovedRequest } from "@/lib/approval-workflow";

// Real, read-only ground-fact bridge for the 3 in-scope planner
// capabilities (castle.verb.inventory-components, castle.verb.inventory-goals,
// approval.freeze-override -- ontology/platform-console-capabilities.ttl).
// Authenticated the SAME shared-secret-header pattern as the other
// /api/internal/* routes (see cost-report-snapshot/route.ts and
// latency-benchmark-snapshot/route.ts's own header comments for the
// one-time operator provisioning step: `kubectl create secret generic
// platform-capability-state-snapshot-cron-secret --from-literal=secret=...`
// in the `platform-console` namespace, then setting the matching
// `CAPABILITY_STATE_SNAPSHOT_SECRET` env on the console's own Deployment).
// Unlike its two siblings (which are CronJob-fired POST pollers that
// persist a history), this route is a plain on-demand GET: the planner
// bridge (Phase 3/4) needs a fresh read at plan time, not a stored trend
// line, so nothing here is written or accumulated -- every call is a
// genuine live read via the exact real k8sRequest/ConfigMap primitives
// castle.ts/freeze-windows.ts/approval-workflow.ts already use, never
// hardcoded or fabricated data.
function isCronAuthenticated(request: NextRequest): boolean {
  const expected = process.env.CAPABILITY_STATE_SNAPSHOT_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no cron bypass, ever
  const presented = request.headers.get("x-capability-state-snapshot-secret");
  return presented === expected;
}

// The 4 ground predicates the 3 in-scope capabilities actually need
// (pd: vocabulary target for autofde-lab's rdf_domain.py, Phase 3) --
// deliberately not a general fact theory, just this slice's minimum.
export interface CapabilityStateSnapshot {
  orgId: string;
  capturedAt: string;
  facts: {
    /** (deployed castle) -- true iff the real platform-castle-deployment
     * ConfigMap (castle.ts's getCastleDeployment) currently records an
     * image. */
    deployedCastle: boolean;
    /** (frozen <org>) -- true iff freeze-windows.ts's getActiveFreeze
     * finds a real, currently-active freeze window for this org. */
    frozenOrg: boolean;
    /** (freeze-override-approved <org>) -- true iff a fresh, real
     * approved "freeze.override" row exists for this org
     * (approval-workflow.ts's findApprovedRequest, same APPROVAL_TTL_HOURS
     * freshness window checkFreezeGuard itself uses). */
    freezeOverrideApprovedOrg: boolean;
    /** (job-complete <verb>) for each allowlisted castle verb -- true iff
     * the most recently created real batch/v1 Job labeled with that verb
     * (castle.ts's listCastleJobs) has status "Complete". `null` when no
     * Job for that verb has ever been run -- distinct from "ran and
     * failed"/"still running", never coerced to false. */
    jobComplete: Record<AllowedCastleVerbId, boolean | null>;
  };
}

function mostRecentJobForVerb(jobs: CastleJob[], verbId: AllowedCastleVerbId): CastleJob | null {
  const matching = jobs.filter((j) => j.verbId === verbId);
  if (matching.length === 0) return null;
  return matching.sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0];
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  if (!isCronAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  // `orgId` travels as a header, the same free-text-but-allowlisted
  // convention its two siblings use for namespace/org -- validated
  // against the same fixed SCHEDULABLE_NAMESPACES allowlist, never
  // trusted as free-form request text.
  const orgId = request.headers.get("x-capability-state-org") ?? "";
  if (!isSchedulableNamespace(orgId)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "capability-state-snapshot",
      method: "GET",
      path: "/api/internal/capability-state-snapshot",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "x-capability-state-org header must be one of the platform's own namespaces" },
      { status: 400 },
    );
  }

  const [deploymentResult, freezeResult, overrideResult, jobsResult] = await Promise.all([
    getCastleDeployment(),
    getActiveFreeze(orgId),
    findApprovedRequest("freeze.override", orgId),
    listCastleJobs(),
  ]);

  for (const result of [deploymentResult, freezeResult, overrideResult, jobsResult]) {
    if (!result.ok) {
      writeAuditLogEntry({
        timestamp: new Date().toISOString(),
        actor: "capability-state-snapshot",
        method: "GET",
        path: "/api/internal/capability-state-snapshot",
        status: 502,
        requestId,
      });
      return NextResponse.json({ error: result.error }, { status: 502 });
    }
  }

  const jobs = jobsResult.ok ? jobsResult.data : [];
  const jobComplete = {} as Record<AllowedCastleVerbId, boolean | null>;
  for (const verbId of Object.keys(ALLOWED_CASTLE_VERBS) as AllowedCastleVerbId[]) {
    const latest = mostRecentJobForVerb(jobs, verbId);
    jobComplete[verbId] = latest === null ? null : latest.status === "Complete";
  }

  const snapshot: CapabilityStateSnapshot = {
    orgId,
    capturedAt: new Date().toISOString(),
    facts: {
      deployedCastle: deploymentResult.ok && deploymentResult.data !== null,
      frozenOrg: freezeResult.ok && freezeResult.data !== null,
      freezeOverrideApprovedOrg: overrideResult.ok && overrideResult.data !== null,
      jobComplete,
    },
  };

  writeAuditLogEntry({
    timestamp: new Date().toISOString(),
    actor: "capability-state-snapshot",
    method: "GET",
    path: "/api/internal/capability-state-snapshot",
    status: 200,
    requestId,
  });

  return NextResponse.json({ snapshot }, { status: 200 });
}
