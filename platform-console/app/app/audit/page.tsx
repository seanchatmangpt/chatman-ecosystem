import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import AuditLogPanel from "@/components/AuditLogPanel";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { queryAuditLog } from "@/lib/audit-db";
import { hasClusterCredentials } from "@/lib/k8s";

export const dynamic = "force-dynamic";

// Owner-only page (same boundary as /org -- audit trail visibility is
// itself sensitive): real, queryable "who did what" history read straight
// from platform_console.audit_log on the live demo-project Postgres
// (lib/audit-db.ts), the durable counterpart to the real ephemeral stdout
// line every authenticated request already produces (lib/audit-log.ts,
// still tailable via /logs or `kubectl logs`). middleware.ts already
// guarantees a valid session reaches this page; the check below is this
// page's OWN role gate on top of that -- but the real enforcement boundary
// for the underlying data is /api/audit's own server-side
// requireRole(session, "owner") call, not this page's rendering.
export default async function AuditPage() {
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

  const access = await requireRole(session, "owner");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Audit Log</h1>
        <p className="mb-8 max-w-3xl text-sm text-gray-400">
          Real hyperscaler CloudTrail / GCP Audit Logs / Azure Monitor Activity Log equivalent:
          a durable, queryable record of authenticated requests, backed by one real{" "}
          <code>platform_console.audit_log</code> table on the live demo-project Postgres this
          cluster already runs -- the same database{" "}
          <code>/projects/[name]/backups</code> trusts with real tenant data. Every entry here
          also exists as a real JSON line on <code>platform-console-gateway</code>&apos;s stdout
          (see <code>/logs</code> or <code>kubectl logs</code>) -- this table exists because that
          line does not survive a pod restart and cannot be filtered or paginated. Owner-only,
          enforced server-side by <code>lib/authz.ts</code>&apos;s <code>requireRole</code>, same
          as <code>/org</code>.
        </p>

        {!clusterConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: no in-cluster ServiceAccount credentials found. This page only
            returns real data when running as the platform-console pod.
          </div>
        )}

        {clusterConfigured && !access.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{access.role}</code>) does not meet the required minimum role (
              <code>owner</code>) for this page.
            </p>
          </div>
        )}

        {clusterConfigured && access.ok && <AuditLogPanelServerBoundary />}
      </main>
    </>
  );
}

async function AuditLogPanelServerBoundary() {
  const result = await queryAuditLog({ limit: 50, offset: 0 });

  if (!result.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {result.error}
      </p>
    );
  }

  return (
    <AuditLogPanel
      initialEntries={result.data.rows}
      initialTotal={result.data.total}
      initialLimit={50}
    />
  );
}
