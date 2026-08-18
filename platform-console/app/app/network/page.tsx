import Nav from "@/components/Nav";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { hasClusterCredentials } from "@/lib/k8s";
import { getNetworkTopology, type ReachabilityCell } from "@/lib/network";

export const dynamic = "force-dynamic";

// The platform's own namespaces -- same list app/topology/page.tsx,
// app/service-discovery/page.tsx, app/registry/page.tsx, app/logs/page.tsx,
// and app/usage/page.tsx use.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

function cellClass(cell: ReachabilityCell): string {
  if (cell.source === cell.target) {
    return cell.verdict === "allow"
      ? "bg-emerald-950/40 text-emerald-300"
      : "bg-red-950/40 text-red-300";
  }
  return cell.verdict === "allow"
    ? "bg-emerald-950/60 text-emerald-300 font-medium"
    : "bg-red-950/60 text-red-300";
}

export default async function NetworkPage() {
  const clusterConfigured = hasClusterCredentials();

  const snapshot = clusterConfigured ? await getNetworkTopology(PLATFORM_NAMESPACES) : null;

  const cellByPair = new Map<string, ReachabilityCell>();
  if (snapshot) {
    for (const cell of snapshot.reachability.cells) {
      cellByPair.set(`${cell.source}->${cell.target}`, cell);
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Network Topology</h1>
        <p className="mb-6 max-w-3xl text-sm text-muted-foreground">
          The AWS VPC console / GCP VPC Network Topology / Azure Virtual Network
          equivalent: real Pod/Service CIDR ranges, a real per-namespace ingress
          reachability matrix computed only from actually-applied{" "}
          <code>NetworkPolicy</code> objects, and the real Istio mTLS trust
          boundary -- one place, not scattered across{" "}
          <code>/service-discovery</code>, <code>/iam</code>, and{" "}
          <code>/topology</code>.
        </p>

        {!clusterConfigured && (
          <Alert className="mb-6 border-amber-900 bg-amber-950/40 text-amber-300">
            <AlertDescription className="text-amber-300">
              not configured: no in-cluster ServiceAccount credentials found.
              This page only returns real data when running as the
              platform-console pod.
            </AlertDescription>
          </Alert>
        )}

        {snapshot && (snapshot.cidrError || snapshot.policyError || snapshot.peerAuthError) && (
          <div className="mb-6 space-y-2">
            {snapshot.cidrError && (
              <Alert variant="destructive">
                <AlertDescription>cidr: {snapshot.cidrError}</AlertDescription>
              </Alert>
            )}
            {snapshot.policyError && (
              <Alert variant="destructive">
                <AlertDescription>networkpolicies: {snapshot.policyError}</AlertDescription>
              </Alert>
            )}
            {snapshot.peerAuthError && (
              <Alert variant="destructive">
                <AlertDescription>peerauthentications: {snapshot.peerAuthError}</AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {snapshot && (
          <>
            {/* ------------------------------------------------------ CIDR */}
            <h2 className="mb-3 text-base font-medium text-foreground">
              Pod / Service CIDR ranges
            </h2>
            <div className="mb-8 grid gap-4 md:grid-cols-2">
              <Card className="p-4">
                <h3 className="mb-1 text-sm font-medium text-foreground">Pod CIDR</h3>
                <p className="mb-3 text-xs text-muted-foreground">
                  Method: {snapshot.cidr.podCidr.method}
                </p>
                <div className="mb-3 space-y-1">
                  {snapshot.cidr.podCidr.authoritative.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      no Node objects visible
                    </p>
                  ) : (
                    snapshot.cidr.podCidr.authoritative.map((n) => (
                      <p key={n.name} className="font-mono text-sm text-foreground">
                        {n.name}: {n.podCIDRs.join(", ") || "(none allocated)"}
                      </p>
                    ))
                  )}
                </div>
                <p className="text-xs text-muted-foreground">
                  Observed (live Pod IPs, {snapshot.cidr.podCidr.observed.sampleCount} sample
                  {snapshot.cidr.podCidr.observed.sampleCount === 1 ? "" : "s"}):{" "}
                  <span className="font-mono text-foreground">
                    {snapshot.cidr.podCidr.observed.cidr ?? "—"}
                  </span>
                  {snapshot.cidr.podCidr.observed.min && (
                    <>
                      {" "}
                      (min {snapshot.cidr.podCidr.observed.min}, max{" "}
                      {snapshot.cidr.podCidr.observed.max})
                    </>
                  )}
                </p>
              </Card>

              <Card className="p-4">
                <h3 className="mb-1 text-sm font-medium text-foreground">Service CIDR</h3>
                <p className="mb-3 text-xs text-muted-foreground">
                  Method: {snapshot.cidr.serviceCidr.method}
                </p>
                <p className="text-sm text-foreground">
                  Observed (live Service ClusterIPs, {snapshot.cidr.serviceCidr.observed.sampleCount}{" "}
                  sample{snapshot.cidr.serviceCidr.observed.sampleCount === 1 ? "" : "s"}):{" "}
                  <span className="font-mono">
                    {snapshot.cidr.serviceCidr.observed.cidr ?? "—"}
                  </span>
                </p>
                {snapshot.cidr.serviceCidr.observed.min && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    min {snapshot.cidr.serviceCidr.observed.min}, max{" "}
                    {snapshot.cidr.serviceCidr.observed.max}
                  </p>
                )}
              </Card>
            </div>

            {/* ------------------------------------------------- mTLS */}
            <h2 className="mb-3 text-base font-medium text-foreground">
              Istio mTLS trust boundary
            </h2>
            <Card className="mb-8 overflow-hidden p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Namespace</TableHead>
                    <TableHead>Namespace-wide mode</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Workload-scoped overrides</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {snapshot.mtls.map((row) => (
                    <TableRow key={row.namespace}>
                      <TableCell className="font-mono text-sm">{row.namespace}</TableCell>
                      <TableCell>
                        {row.namespaceWide ? (
                          <span
                            className={
                              row.namespaceWide.mode === "STRICT"
                                ? "font-medium text-emerald-400"
                                : "font-medium text-amber-400"
                            }
                          >
                            {row.namespaceWide.mode ?? "(unset)"}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">no PeerAuthentication</span>
                        )}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {row.namespaceWide ? row.namespaceWide.name : "mesh default applies"}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {row.workloadOverrides.length === 0
                          ? "none"
                          : row.workloadOverrides
                              .map((o) => `${o.name} (${o.mode ?? "unset"})`)
                              .join(", ")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
            <p className="mb-8 -mt-4 text-xs text-muted-foreground">
              Namespaces with no PeerAuthentication object are shown honestly as
              such -- confirming Istio&apos;s documented mesh-wide PERMISSIVE
              fallback would require reading the <code>istio</code> ConfigMap in
              <code> istio-system</code>, which this console deliberately has no
              RBAC into.
            </p>

            {/* ------------------------------------------- Reachability */}
            <h2 className="mb-3 text-base font-medium text-foreground">
              Namespace-to-namespace ingress reachability
            </h2>
            <p className="mb-3 text-xs text-muted-foreground">
              Rows are the source namespace, columns are the target. Computed
              only from real, actually-applied <code>NetworkPolicy</code>{" "}
              objects (<code>ingressFromNamespaces</code>, reused from{" "}
              <code>lib/k8s.ts</code>&apos;s <code>listNetworkPolicies</code>) --
              hover a cell for the exact policy name(s) it was decided from.
            </p>
            <Card className="mb-4 overflow-hidden p-3">
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-xs">
                  <thead>
                    <tr>
                      <th className="p-2 text-left text-muted-foreground">
                        source \ target
                      </th>
                      {snapshot.reachability.namespaces.map((target) => (
                        <th
                          key={target}
                          className="p-2 text-left font-mono font-medium text-foreground"
                        >
                          {target}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {snapshot.reachability.namespaces.map((source) => (
                      <tr key={source}>
                        <td className="p-2 font-mono font-medium text-foreground">{source}</td>
                        {snapshot.reachability.namespaces.map((target) => {
                          const cell = cellByPair.get(`${source}->${target}`);
                          if (!cell) return <td key={target} className="p-2">—</td>;
                          return (
                            <td key={target} className="p-1">
                              <div
                                title={cell.reason}
                                className={`rounded px-2 py-1.5 text-center font-mono ${cellClass(cell)}`}
                              >
                                {cell.verdict === "allow" ? "allow" : "deny"}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
            <div className="mb-8 flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded bg-emerald-600" /> allow
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded bg-red-700" /> deny
              </span>
            </div>
          </>
        )}
      </main>
    </>
  );
}
