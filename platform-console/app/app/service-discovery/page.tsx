import Nav from "@/components/Nav";
import TagEditor from "@/components/TagEditor";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  hasClusterCredentials,
  listServicesWithEndpoints,
  type ServiceDiscoveryRecord,
} from "@/lib/k8s";
import { extractTags } from "@/lib/tags";

export const dynamic = "force-dynamic";

// The platform's own namespaces -- the 4 project namespaces, supabase-demo,
// and platform-console's own namespace. Same list app/registry/page.tsx,
// app/logs/page.tsx, and app/usage/page.tsx use.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

function formatPorts(ports: ServiceDiscoveryRecord["ports"]): string {
  if (ports.length === 0) return "—";
  return ports
    .map((p) => {
      const name = p.name ? `${p.name}:` : "";
      const target = p.targetPort !== undefined ? `→${p.targetPort}` : "";
      return `${name}${p.port}/${p.protocol}${target}`;
    })
    .join(", ");
}

function EndpointsBadge({ ready, total }: { ready: number | null; total: number | null }) {
  if (ready === null || total === null) {
    return (
      <Badge variant="outline" className="gap-1.5 text-muted-foreground">
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
        no Endpoints object
      </Badge>
    );
  }
  if (total === 0) {
    return (
      <Badge variant="outline" className="gap-1.5 border-red-900 bg-red-950/40 text-red-300">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
        0/0
      </Badge>
    );
  }
  if (ready === 0) {
    return (
      <Badge variant="outline" className="gap-1.5 border-red-900 bg-red-950/40 text-red-300">
        <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
        0/{total} ready
      </Badge>
    );
  }
  if (ready < total) {
    return (
      <Badge variant="outline" className="gap-1.5 border-amber-900 bg-amber-950/40 text-amber-300">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
        {ready}/{total} ready
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="gap-1.5 border-emerald-900 bg-emerald-950/40 text-emerald-300">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
      {ready}/{total} ready
    </Badge>
  );
}

export default async function ServiceDiscoveryPage() {
  const clusterConfigured = hasClusterCredentials();

  const rows: Array<{ namespace: string; records: ServiceDiscoveryRecord[] }> = [];
  const errors: Array<{ namespace: string; error: string }> = [];

  if (clusterConfigured) {
    const results = await Promise.all(
      PLATFORM_NAMESPACES.map(async (namespace) => ({
        namespace,
        result: await listServicesWithEndpoints(namespace),
      })),
    );
    for (const { namespace, result } of results) {
      if (result.ok) {
        rows.push({ namespace, records: result.data });
      } else {
        errors.push({ namespace, error: result.error });
      }
    }
  }

  const allRecords = rows.flatMap((r) => r.records);
  const zeroReadyCount = allRecords.filter(
    (r) => r.totalEndpoints !== null && r.totalEndpoints > 0 && r.readyEndpoints === 0,
  ).length;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Service Discovery</h1>

        <Alert className="mb-6 border-blue-900 bg-blue-950/30 text-blue-200">
          <AlertDescription className="text-blue-200">
            <strong>Real cluster-internal DNS, not a decorative view.</strong>{" "}
            The AWS Route53 private hosted zone / GCP Cloud DNS internal zone /
            Azure Private DNS equivalent here is CoreDNS plus every real k8s{" "}
            <code>Service</code>/<code>Endpoints</code> object -- the exact
            mechanism every other module&apos;s cluster-internal URLs already
            depend on (the Database module&apos;s Postgres/PostgREST hosts, the
            Backups module&apos;s <code>pg_dump</code> target). CoreDNS answers{" "}
            <code>&lt;svc&gt;.&lt;namespace&gt;.svc.cluster.local</code> from
            these same two objects, read live below via the k8s API -- never a
            separate DNS-specific API or a fabricated record.{" "}
            <strong>Ready endpoints</strong> is the load-bearing signal: how
            many backing Pod IPs are actually passing readiness right now, i.e.
            whether that DNS name currently resolves to something healthy.
          </AlertDescription>
        </Alert>

        {!clusterConfigured && (
          <Alert className="mb-6 border-amber-900 bg-amber-950/40 text-amber-300">
            <AlertDescription className="text-amber-300">
              not configured: no in-cluster ServiceAccount credentials found.
              This page only returns real data when running as the
              platform-console pod.
            </AlertDescription>
          </Alert>
        )}

        {errors.length > 0 && (
          <div className="mb-6 space-y-2">
            {errors.map((e) => (
              <Alert key={e.namespace} variant="destructive">
                <AlertDescription>
                  {e.namespace}: {e.error}
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {clusterConfigured && allRecords.length > 0 && (
          <p className="mb-4 text-xs text-muted-foreground">
            {allRecords.length} Service(s) across {rows.length} namespaces --{" "}
            {zeroReadyCount === 0 ? (
              <span className="text-emerald-400">0 with zero ready endpoints</span>
            ) : (
              <span className="text-red-400">
                {zeroReadyCount} with zero ready endpoints
              </span>
            )}
            .
          </p>
        )}

        <Card className="overflow-x-auto">
          <Table className="min-w-[900px]">
            <TableHeader>
              <TableRow>
                <TableHead>Namespace</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>DNS name</TableHead>
                <TableHead>ClusterIP</TableHead>
                <TableHead>Ports</TableHead>
                <TableHead>Ready endpoints</TableHead>
                <TableHead>Tags</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {allRecords.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="py-6 text-sm text-muted-foreground">
                    {clusterConfigured ? "No Services found." : "—"}
                  </TableCell>
                </TableRow>
              )}
              {rows.map(({ namespace, records }) =>
                records.map((r) => (
                  <TableRow key={`${namespace}/${r.name}`}>
                    <TableCell className="text-muted-foreground">
                      <code>{namespace}</code>
                    </TableCell>
                    <TableCell className="text-foreground">{r.name}</TableCell>
                    <TableCell>
                      <code className="text-xs text-foreground">{r.dns}</code>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      <code className="text-xs">{r.clusterIP ?? "—"}</code>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      <code className="text-xs">{formatPorts(r.ports)}</code>
                    </TableCell>
                    <TableCell>
                      <EndpointsBadge ready={r.readyEndpoints} total={r.totalEndpoints} />
                    </TableCell>
                    <TableCell className="min-w-[200px]">
                      <TagEditor
                        resourceType="service"
                        namespace={namespace}
                        name={r.name}
                        initialTags={extractTags(r.labels)}
                      />
                    </TableCell>
                  </TableRow>
                )),
              )}
            </TableBody>
          </Table>
        </Card>

        <p className="mt-4 text-xs text-muted-foreground">
          &quot;Ready endpoints&quot; is <code>subsets[].addresses.length</code>{" "}
          on the real <code>core/v1 Endpoints</code> object matching each
          Service&apos;s name (the endpoint-controller&apos;s own naming
          convention); &quot;total&quot; adds{" "}
          <code>subsets[].notReadyAddresses.length</code> -- Pod IPs the
          Service selects but that have not yet passed a readiness probe.
          &quot;no Endpoints object&quot; means no Endpoints resource exists
          for that Service name at all (a selector matching nothing), distinct
          from a real 0/0.
        </p>
      </main>
    </>
  );
}
