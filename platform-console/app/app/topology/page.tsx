import Link from "next/link";
import Nav from "@/components/Nav";
import DeckTopology from "@/components/DeckTopology";
import IsoflowTopology from "@/components/IsoflowTopology";
import MermaidDiagram from "@/components/MermaidDiagram";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  hasClusterCredentials,
  listNetworkPolicies,
  listServicesWithEndpoints,
  type IamNetworkPolicy,
  type ServiceDiscoveryRecord,
} from "@/lib/k8s";
import { buildFlowchartInput, buildTopologySnapshot } from "@/lib/topology";
import { buildIsoflowModel } from "@/lib/isoflow-model";
import { renderFlowchart } from "@/lib/mermaid";

export const dynamic = "force-dynamic";

// The platform's own namespaces -- same list app/service-discovery/page.tsx,
// app/registry/page.tsx, app/logs/page.tsx, and app/usage/page.tsx use.
const PLATFORM_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];

export default async function TopologyPage() {
  const clusterConfigured = hasClusterCredentials();

  const rows: Array<{ namespace: string; records: ServiceDiscoveryRecord[] }> = [];
  const errors: Array<{ namespace: string; error: string }> = [];
  let policyError: string | null = null;
  let policies: IamNetworkPolicy[] = [];

  if (clusterConfigured) {
    const [serviceResults, policyResult] = await Promise.all([
      Promise.all(
        PLATFORM_NAMESPACES.map(async (namespace) => ({
          namespace,
          result: await listServicesWithEndpoints(namespace),
        })),
      ),
      listNetworkPolicies(),
    ]);
    for (const { namespace, result } of serviceResults) {
      if (result.ok) {
        rows.push({ namespace, records: result.data });
      } else {
        errors.push({ namespace, error: result.error });
      }
    }
    if (policyResult.ok) {
      policies = policyResult.data;
    } else {
      policyError = policyResult.error;
    }
  }

  const snapshot = buildTopologySnapshot(rows, policies);
  const totalServices = snapshot.nodes.length;
  const zeroReadyCount = snapshot.nodes.filter(
    (n) => n.totalEndpoints !== null && n.totalEndpoints > 0 && n.readyEndpoints === 0,
  ).length;
  // Same `rows`/`policies` inputs as `buildTopologySnapshot` above -- the
  // isoflow model is a re-projection of the exact same snapshot data, so
  // its node/namespace/edge counts match the deck.gl view by construction.
  const { model: isoflowModel, serviceIconId, serviceIconFallback } = buildIsoflowModel(rows, policies);

  // Same `snapshot` the deck.gl/isoflow tabs above render, re-projected to
  // one namespace-level flowchart and rendered to real Mermaid text via
  // mmdio's typed FlowchartDiagram model (lib/mermaid.ts) -- not a
  // hand-built diagram string.
  const flowchartInput = buildFlowchartInput(snapshot);
  const mermaidResult =
    flowchartInput.nodes.length > 0 ? renderFlowchart(flowchartInput) : null;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-6xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-foreground">Cluster Topology</h1>

        <Alert className="mb-6 border-blue-900 bg-blue-950/30 text-blue-200">
          <AlertDescription className="text-blue-200">
            <strong>Real cluster data, not a decorative diagram.</strong> Nodes
            are the exact <code>Service</code>/<code>Endpoints</code> records{" "}
            <Link href="/service-discovery" className="underline underline-offset-2">
              Service Discovery
            </Link>{" "}
            already renders as a table -- same <code>listServicesWithEndpoints</code>{" "}
            call, same ready-endpoint counts. Position is a deterministic
            grid-per-namespace layout computed in code (
            <code>lib/topology.ts</code>), not a random or physics-stepped
            force simulation -- the same input always produces the same
            picture. Arcs are drawn only where a real{" "}
            <code>NetworkPolicy</code> ingress rule names a source namespace
            via <code>namespaceSelector</code> (
            <code>k8s/network-policies.yaml</code>&apos;s{" "}
            <code>*-allow-from-platform-console</code> rules) -- there is no
            geospatial meaning here (this is not a map), so the view is a
            plain 2D <code>OrthographicView</code>, not deck.gl&apos;s
            longitude/latitude <code>MapView</code>.
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

        {(errors.length > 0 || policyError) && (
          <div className="mb-6 space-y-2">
            {errors.map((e) => (
              <Alert key={e.namespace} variant="destructive">
                <AlertDescription>
                  {e.namespace}: {e.error}
                </AlertDescription>
              </Alert>
            ))}
            {policyError && (
              <Alert variant="destructive">
                <AlertDescription>networkpolicies: {policyError}</AlertDescription>
              </Alert>
            )}
          </div>
        )}

        {clusterConfigured && totalServices > 0 && (
          <p className="mb-4 text-xs text-muted-foreground">
            {totalServices} Service(s) across {snapshot.clusters.length} namespaces,{" "}
            {snapshot.edges.length} real cross-namespace ingress-allow edge(s) --{" "}
            {zeroReadyCount === 0 ? (
              <span className="text-emerald-400">0 with zero ready endpoints</span>
            ) : (
              <span className="text-red-400">{zeroReadyCount} with zero ready endpoints</span>
            )}
            .
          </p>
        )}

        <Card className="p-3">
          {totalServices === 0 ? (
            <p className="p-6 text-sm text-muted-foreground">
              {clusterConfigured ? "No Services found." : "—"}
            </p>
          ) : (
            <Tabs defaultValue="spatial">
              <TabsList>
                <TabsTrigger value="spatial">Spatial (deck.gl)</TabsTrigger>
                <TabsTrigger value="isometric">Isometric (isoflow)</TabsTrigger>
                <TabsTrigger value="mermaid">Mermaid (mmdio)</TabsTrigger>
              </TabsList>
              <TabsContent value="spatial">
                <DeckTopology
                  nodes={snapshot.nodes}
                  clusters={snapshot.clusters}
                  edges={snapshot.edges}
                />
              </TabsContent>
              <TabsContent value="isometric">
                <IsoflowTopology model={isoflowModel} />
                <p className="mt-2 text-xs text-muted-foreground">
                  Same {isoflowModel.items.length} Service node(s) across{" "}
                  {isoflowModel.views[0]?.rectangles?.length ?? 0} namespace region(s),{" "}
                  {isoflowModel.views[0]?.connectors?.length ?? 0} real NetworkPolicy
                  connector(s) -- icon: <code>{serviceIconId}</code>
                  {serviceIconFallback ? " (generic fallback, k8s-svc unavailable)" : " (Kubernetes isopack)"}.
                </p>
              </TabsContent>
              <TabsContent value="mermaid">
                {mermaidResult === null ? (
                  <p className="p-6 text-sm text-muted-foreground">No namespace clusters to render.</p>
                ) : mermaidResult.ok ? (
                  <MermaidDiagram source={mermaidResult.data} />
                ) : (
                  <Alert variant="destructive" className="m-3">
                    <AlertDescription>mmdio render-flowchart: {mermaidResult.error}</AlertDescription>
                  </Alert>
                )}
                <p className="mt-2 text-xs text-muted-foreground">
                  Real Mermaid flowchart text, rendered by mmdio&apos;s typed{" "}
                  <code>FlowchartDiagram</code> Pydantic model (
                  <code>render_diagram()</code>) via a subprocess call to{" "}
                  <code>mmdio render-flowchart</code> (<code>lib/mermaid.ts</code>) -- one
                  node per namespace cluster, one edge per distinct cross-namespace
                  NetworkPolicy ingress-allow pair, same {snapshot.clusters.length}{" "}
                  cluster(s) / {snapshot.edges.length} edge(s) the summary line above counts.
                </p>
              </TabsContent>
            </Tabs>
          )}
        </Card>

        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#0ca30c" }} />
            all endpoints ready
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#fab219" }} />
            partially ready
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#d03b3b" }} />
            zero ready / 0 total
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: "#898781" }} />
            no Endpoints object
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4" style={{ background: "#3987e5" }} />
            NetworkPolicy ingress-allow (cross-namespace)
          </span>
          <span>
            Node size scales with ready-endpoint count. Drag to pan, scroll to zoom, click a
            node to pin its detail panel. Full tabular view:{" "}
            <Link href="/service-discovery" className="underline underline-offset-2">
              /service-discovery
            </Link>
            .
          </span>
        </div>
      </main>
    </>
  );
}
