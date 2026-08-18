import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import LogSearchPanel from "@/components/LogSearchPanel";

export const dynamic = "force-dynamic";

// The real CloudWatch Logs Insights / GCP Cloud Logging / Azure Log
// Analytics equivalent this platform previously had no equivalent for:
// cross-pod, cross-namespace, queryable log search. /logs (per-pod
// kubectl-logs tail) stays as-is for a single pod's own stdout/stderr --
// this page is additive, not a replacement, and answers a different
// question ("show me every line matching X across the whole platform")
// that a per-pod tail structurally cannot.
//
// Backed by a real Loki instance (k8s/loki-log-aggregation.yaml,
// monitoring namespace, single-binary/filesystem-storage target sized for
// this single-node cluster) fed by a real Promtail DaemonSet that tails
// every container log file on the node (/var/log/pods) and ships it in,
// labeled namespace/pod/container/node. lib/loki.ts proxies Loki's own
// LogQL query_range API server-side; nothing here is synthesized.
//
// Viewer-and-up read access (requireRole "viewer"), same boundary as
// /tracing -- log content is operational telemetry, not an access record
// like /audit's owner-only gate.
export default async function LogSearchPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <Alert variant="destructive">
            <AlertDescription>unauthenticated</AlertDescription>
          </Alert>
        </main>
      </>
    );
  }

  const access = await requireRole(session, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Log Search</h1>
        <p className="mb-8 max-w-3xl text-sm text-muted-foreground">
          Real hyperscaler CloudWatch Logs Insights / GCP Cloud Logging / Azure Log Analytics
          equivalent: cross-pod, cross-namespace log search over every container this cluster
          runs, backed by a real Loki instance (<code>k8s/loki-log-aggregation.yaml</code>) fed
          live by a Promtail DaemonSet. Queried server-side via Loki&apos;s own LogQL{" "}
          <code>query_range</code> API (
          <code>loki.monitoring.svc.cluster.local:3100</code>) -- nothing here is synthesized.
          For a single pod&apos;s live tail, see <code>/logs</code>. Viewer-and-up read access,
          enforced server-side by <code>lib/authz.ts</code>&apos;s <code>requireRole</code>, same
          mechanism as <code>/tracing</code>.
        </p>

        {!access.ok && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>
              403 -- forbidden. Your role (<code>{access.role}</code>) does not meet the required
              minimum role (<code>viewer</code>) for this page.
            </AlertDescription>
          </Alert>
        )}

        {access.ok && (
          <Card>
            <CardHeader>
              <h2 className="text-base font-medium text-foreground">Search</h2>
            </CardHeader>
            <CardContent>
              <LogSearchPanel />
            </CardContent>
          </Card>
        )}
      </main>
    </>
  );
}
