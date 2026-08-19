import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import CompliancePanel from "@/components/CompliancePanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { hasClusterCredentials } from "@/lib/k8s";
import {
  getComplianceCadence,
  listComplianceReports,
  CADENCE_CRON_SCHEDULE,
} from "@/lib/compliance-report";

export const dynamic = "force-dynamic";

// Real Scheduled Compliance Report settings + history page for this
// deployment's one real single-tenant org (IP_ALLOWLIST_NAMESPACE /
// ORG_ROLES_NAMESPACE's own "platform-console" fallback, same convention
// app/org/security/page.tsx already uses for its own single-tenant IP
// allowlist page). Server component gates rendering the same way -- a
// non-member sees a real 403 message, not the panel; every actual
// mutation (PUT cadence, POST generate) is re-checked by the API route
// regardless of what this page renders.
const ORG_ID = "platform-console";

export default async function OrgCompliancePage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  const clusterConfigured = hasClusterCredentials();

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            unauthenticated
          </p>
        </main>
      </>
    );
  }

  const orgResult = await getOrg(ORG_ID);
  const namespace = orgResult.ok && orgResult.data ? orgResult.data.namespace : ORG_ID;

  const viewerAccess = await requireRoleIn(session, namespace, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Scheduled compliance reports</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          A real, dated, self-contained report -- audit event count, IP allowlist snapshot, cost
          anomalies detected in the period, and active admission-policy bindings -- generated on a
          recurring k8s CronJob cadence or on demand. Stored in the real{" "}
          <code>platform-compliance-reports</code> ConfigMap (<code>platform-console</code>{" "}
          namespace); the full audit-trail NDJSON is streamed live from Postgres at download time,
          never held in the ConfigMap itself.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only returns
            real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && !viewerAccess.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{viewerAccess.role}</code>) does not meet the required minimum role
              (<code>viewer</code>) to view this org&apos;s compliance reports.
            </p>
          </div>
        )}

        {clusterConfigured && viewerAccess.ok && (
          <CompliancePanelServerBoundary
            orgId={ORG_ID}
            namespace={namespace}
            actorRole={viewerAccess.role}
          />
        )}
      </main>
    </>
  );
}

async function CompliancePanelServerBoundary({
  orgId,
  namespace,
  actorRole,
}: {
  orgId: string;
  namespace: string;
  actorRole: "viewer" | "member" | "owner";
}) {
  const [reportsResult, cadenceResult] = await Promise.all([
    listComplianceReports(orgId),
    getComplianceCadence(orgId),
  ]);

  if (!reportsResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read reports: {reportsResult.error}
      </p>
    );
  }
  if (!cadenceResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        failed to read cadence: {cadenceResult.error}
      </p>
    );
  }

  const reports = reportsResult.data.map((r) => ({
    reportId: r.reportId,
    periodStart: r.periodStart,
    periodEnd: r.periodEnd,
    generatedAt: r.generatedAt,
    generatedBy: r.generatedBy,
    sections: r.sections,
    downloadUrl: `/api/orgs/${orgId}/compliance-reports/${r.reportId}?format=json`,
    csvUrl: `/api/orgs/${orgId}/compliance-reports/${r.reportId}?format=csv`,
    ndjsonUrl: `/api/orgs/${orgId}/compliance-reports/${r.reportId}?format=ndjson`,
  }));

  return (
    <CompliancePanel
      orgId={orgId}
      namespace={namespace}
      cadence={cadenceResult.data}
      cronSchedule={cadenceResult.data ? CADENCE_CRON_SCHEDULE[cadenceResult.data.interval] : null}
      reports={reports}
      canManageCadence={actorRole === "owner"}
      canGenerate={actorRole === "member" || actorRole === "owner"}
    />
  );
}
