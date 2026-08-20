import { NextRequest, NextResponse } from "next/server";
import { newRequestId, writeAuditLogEntry } from "@/lib/audit-db";
import {
  listOrgs,
  getOrg,
  getOrgProjectTier,
  type Org,
} from "@/lib/orgs";
import {
  listProjects,
  listSecrets,
  listDeployments,
  getResourceQuota,
  listNamespaces,
} from "@/lib/k8s";
import { getCastleDeployment } from "@/lib/castle";
import { isFrozenNow, getActiveFreeze } from "@/lib/freeze-windows";
import {
  findApprovedRequest,
  type ApprovalAction,
} from "@/lib/approval-workflow";
import { getReservation } from "@/lib/capacity-reservations";
import { listPartners } from "@/lib/partners";
import { listDsarRequests } from "@/lib/dsar";
import { getOrgPatchSlaBreaches } from "@/lib/patch-sla";

// Real, unattended read-only ground-fact snapshot endpoint -- authenticated
// the SAME shared-secret-header pattern as POST /api/internal/cost-report-
// snapshot and POST /api/internal/latency-benchmark-snapshot (see either
// route's own header comment for the one-time operator provisioning step:
// `kubectl create secret generic platform-capability-state-cron-secret
// --from-literal=secret=...` in the `platform-console` namespace, then
// setting the matching `CAPABILITY_STATE_SNAPSHOT_SECRET` env on the
// console's own Deployment). This route never mutates anything -- every
// call below is a real, live read reusing existing lib/*.ts primitives,
// never a new k8s write/read primitive invented for this route.
function isInternalAuthenticated(request: NextRequest): boolean {
  const expected = process.env.CAPABILITY_STATE_SNAPSHOT_SECRET;
  if (!expected) return false; // fail-closed: no configured secret means no internal bypass, ever
  const presented = request.headers.get("x-capability-state-snapshot-secret");
  return presented === expected;
}

/**
 * One approval-gated capability's real ground-fact state: whether a fresh
 * (<=24h TTL) approved row exists for (action, targetId), reusing
 * lib/approval-workflow.ts's own findApprovedRequest -- never a
 * reimplementation of its TTL/status logic.
 */
async function approvalState(
  action: ApprovalAction,
  targetId: string,
): Promise<{ approved: boolean; approvedAt?: string; approvedBy?: string } | { error: string }> {
  const result = await findApprovedRequest(action, targetId);
  if (!result.ok) return { error: result.error };
  if (!result.data) return { approved: false };
  return { approved: true, approvedAt: result.data.approvedAt, approvedBy: result.data.approvedBy };
}

export async function GET(request: NextRequest) {
  const requestId = newRequestId();
  if (!isInternalAuthenticated(request)) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }

  const orgId = request.nextUrl.searchParams.get("org") ?? "";
  const projectName = request.nextUrl.searchParams.get("project") ?? undefined;
  const partnerId = request.nextUrl.searchParams.get("partner") ?? undefined;

  // `org` validated against the real, live org registry (lib/orgs.ts) --
  // never trusted as free-form request text, same discipline the
  // existing x-cost-report-namespace / x-latency-benchmark-org headers
  // enforce against SCHEDULABLE_NAMESPACES on the sibling internal routes.
  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "capability-state-snapshot",
      method: "GET",
      path: "/api/internal/capability-state-snapshot",
      status: 502,
      requestId,
    });
    return NextResponse.json({ error: orgsResult.error }, { status: 502 });
  }
  const knownOrgIds = new Set(orgsResult.data.map((o) => o.id));
  if (!orgId || !knownOrgIds.has(orgId)) {
    writeAuditLogEntry({
      timestamp: new Date().toISOString(),
      actor: "capability-state-snapshot",
      method: "GET",
      path: "/api/internal/capability-state-snapshot",
      status: 400,
      requestId,
    });
    return NextResponse.json(
      { error: "org query param must be a real, registered org id (see GET /api/orgs)" },
      { status: 400 },
    );
  }

  const orgResult = await getOrg(orgId);
  const org: Org | null = orgResult.ok ? orgResult.data : null;
  const namespace = org?.namespace ?? null;

  // --- CASTLE ---------------------------------------------------------
  const castleDeployment = await getCastleDeployment();

  // --- ORG / FREEZE / RESERVATION / DSAR / PATCH-SLA ------------------
  const [
    frozenNow,
    activeFreeze,
    reservation,
    dsarRequests,
    patchSlaBreaches,
    quota,
    secrets,
    deployments,
    projects,
    projectTier,
  ] = await Promise.all([
    isFrozenNow(orgId),
    getActiveFreeze(orgId),
    getReservation(orgId),
    listDsarRequests(orgId),
    getOrgPatchSlaBreaches(orgId),
    namespace ? getResourceQuota(namespace) : Promise.resolve({ ok: true as const, data: null }),
    namespace ? listSecrets(namespace) : Promise.resolve({ ok: true as const, data: [] }),
    namespace ? listDeployments(namespace) : Promise.resolve({ ok: true as const, data: [] }),
    listProjects(),
    namespace
      ? getOrgProjectTier(namespace)
      : Promise.resolve({ ok: true as const, data: undefined }),
  ]);

  const orgNamespaces = await listNamespaces();
  const namespaceExists = namespace !== null && orgNamespaces.ok
    ? orgNamespaces.data.includes(namespace)
    : null;

  const orgProjects = namespace ? projects.ok ? projects.data.filter((p) => p.namespace === namespace) : [] : [];
  const singleProject = projectName
    ? orgProjects.find((p) => p.name === projectName) ?? null
    : orgProjects[0] ?? null;

  // --- APPROVAL-GATED CAPABILITY STATES --------------------------------
  const approvalTargetId = orgId;
  const [
    orgDeleteApproval,
    quotaOverrideApproval,
    tierDowngradeApproval,
    backupRetentionApproval,
    exportSubscriptionApproval,
    drFailoverApproval,
    dsarErasureApproval,
    castleScheduleApproval,
    freezeOverrideApproval,
    environmentPromoteApproval,
    deploymentQuarantineApproval,
    slaCreditApproval,
    patchSlaCreditApproval,
    k8sFaultRemediateApproval,
  ] = await Promise.all([
    approvalState("org.delete", approvalTargetId),
    approvalState("quota.override", approvalTargetId),
    approvalState("tier.downgrade", approvalTargetId),
    approvalState("backup.retention.change", approvalTargetId),
    approvalState("export-subscription.update", approvalTargetId),
    approvalState("dr.failover", approvalTargetId),
    approvalState("dsar.erasure", approvalTargetId),
    approvalState("castle.verb.schedule", approvalTargetId),
    approvalState("freeze.override", approvalTargetId),
    approvalState("environment.promote", approvalTargetId),
    approvalState("deployment.quarantine", approvalTargetId),
    approvalState("sla.credit.apply", approvalTargetId),
    approvalState("patch-sla.credit.apply", approvalTargetId),
    approvalState("k8s-fault.remediate-suggest", approvalTargetId),
  ]);

  // --- PARTNER ----------------------------------------------------------
  let partnerExists: boolean | null = null;
  let partnerManagesOrg: boolean | null = null;
  if (partnerId) {
    const partnersResult = await listPartners();
    if (partnersResult.ok) {
      const partner = partnersResult.data.find((p) => p.id === partnerId) ?? null;
      partnerExists = partner !== null;
      partnerManagesOrg = partner ? partner.managedOrgIds.includes(orgId) : false;
    }
  }

  const snapshot = {
    requestId,
    org: orgId,
    generatedAt: new Date().toISOString(),

    // CASTLE
    "deployed(castle)": castleDeployment.ok ? castleDeployment.data !== null : null,
    "castle-deployment": castleDeployment.ok ? castleDeployment.data : null,

    // Org existence / identity
    "org-exists(org)": org !== null,
    "org-namespace": namespace,
    "namespace-exists(org)": namespaceExists,

    // Freeze
    "frozen(org)": frozenNow,
    "active-freeze": activeFreeze.ok ? activeFreeze.data : null,
    "freeze-override-approved(org)": "error" in freezeOverrideApproval ? null : freezeOverrideApproval.approved,

    // Project / tier / quota
    "project-tier(org,project)": projectTier.ok ? projectTier.data ?? null : null,
    "project-exists(org,project)": singleProject !== null,
    "quota-hard(namespace,resource)": quota.ok ? quota.data : null,

    // Reservation
    "reservation-active(org)": reservation.ok ? reservation.data !== null : null,
    "reservation": reservation.ok ? reservation.data : null,

    // Partner
    "partner-exists(id)": partnerExists,
    "partner-manages-org(id,org)": partnerManagesOrg,

    // DSAR
    "dsar-pending(org)": dsarRequests.ok
      ? dsarRequests.data.some((r) => r.status === "pending" || r.status === "processing")
      : null,
    "dsar-requests(org)": dsarRequests.ok ? dsarRequests.data : null,

    // Patch-SLA breaches (real ground fact `patch-sla.credit.apply` acts on)
    "patch-sla-breach-open(org)": patchSlaBreaches.ok
      ? patchSlaBreaches.data.length > 0
      : null,
    "patch-sla-breaches(org)": patchSlaBreaches.ok ? patchSlaBreaches.data : null,

    // SLA-credit idempotency guard (real ground fact `sla.credit.apply` reads)
    "sla-credit-applied-this-month(org)": org?.lastSlaCreditAppliedMonth ?? null,

    // Secrets / deployments (namespace-scoped k8s reads reused verbatim)
    "secrets(namespace)": secrets.ok ? secrets.data.map((s) => s.name) : null,
    "deployments(namespace)": deployments.ok
      ? deployments.data.map((d) => ({
          name: d.name,
          replicasDesired: d.replicasDesired,
          replicasReady: d.replicasReady,
          replicasAvailable: d.replicasAvailable,
        }))
      : null,

    // Approval-gated capability ground states (real fresh-approval lookups,
    // one per ApprovalAction in lib/approval-workflow.ts's
    // ACTIONS_REQUIRING_APPROVAL enumeration -- every action keyed to this
    // org's own id as targetId, the same targetId convention every
    // existing requireApproval caller in this codebase already uses)
    approvals: {
      "org.delete": orgDeleteApproval,
      "quota.override": quotaOverrideApproval,
      "tier.downgrade": tierDowngradeApproval,
      "backup.retention.change": backupRetentionApproval,
      "export-subscription.update": exportSubscriptionApproval,
      "dr.failover": drFailoverApproval,
      "dsar.erasure": dsarErasureApproval,
      "castle.verb.schedule": castleScheduleApproval,
      "freeze.override": freezeOverrideApproval,
      "environment.promote": environmentPromoteApproval,
      "deployment.quarantine": deploymentQuarantineApproval,
      "sla.credit.apply": slaCreditApproval,
      "patch-sla.credit.apply": patchSlaCreditApproval,
      "k8s-fault.remediate-suggest": k8sFaultRemediateApproval,
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

  return NextResponse.json(snapshot);
}
