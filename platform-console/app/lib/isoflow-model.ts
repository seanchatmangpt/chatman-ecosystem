/**
 * Pure conversion of the SAME real topology data `lib/topology.ts` computes
 * (namespaces, Services, real cross-namespace NetworkPolicy-derived edges)
 * into isoflow's real `Model` shape (isoflow@1.1.1 -- verified against the
 * installed package's own zod-derived `.d.ts` files, not the docs prose).
 *
 * This does NOT re-fetch or re-derive topology data: it calls
 * `buildTopologySnapshot` -- the exact function `app/topology/page.tsx`
 * already calls for the deck.gl view -- and re-projects that same
 * `TopologySnapshot` onto isoflow's node/view/rectangle/connector schema.
 * Because both visualizations consume one shared snapshot, their node,
 * namespace, and edge counts are identical by construction, not by
 * coincidence -- there is nothing to keep in sync by hand.
 *
 * Isoflow model shape (real, from `isoflow/dist/schemas/model.d.ts`):
 *   - `items`      -- logical nodes (id/name/description/icon), no position.
 *   - `views[].items`       -- per-view placement of those items (integer
 *                              tile coordinates, not the free pixel
 *                              coordinates `lib/topology.ts` computes).
 *   - `views[].rectangles`  -- namespace regions (one per queried
 *                              namespace, whether or not it has Services).
 *   - `views[].connectors`  -- the real cross-namespace NetworkPolicy
 *                              ingress-allow edges, anchored by tile
 *                              position (namespace-to-namespace, matching
 *                              what `TopologyEdge` actually represents --
 *                              there is no per-Service connector in the
 *                              source data to reuse instead).
 *   - `icons` / `colors`    -- referenced by id from the above.
 */
import { flattenCollections } from "@isoflow/isopacks/dist/utils";
import type { FlattenedIcon } from "@isoflow/isopacks/dist/types";
import isoflowIsopack from "@isoflow/isopacks/dist/isoflow";
import kubernetesIsopack from "@isoflow/isopacks/dist/kubernetes";
import type { Model } from "isoflow";
import type { IamNetworkPolicy, ServiceDiscoveryRecord } from "./k8s";
import { buildTopologySnapshot, type TopologyNode } from "./topology";

/**
 * `lib/topology.ts` lays nodes out on a continuous pixel plane
 * (`CLUSTER_SPACING = 420`, ring radii in the tens/hundreds of pixels).
 * isoflow's grid is integer tile coordinates. This is a linear projection
 * of the SAME real x/y values onto that integer grid -- dividing and
 * rounding, not inventing new positions -- chosen so a `CLUSTER_SPACING`
 * gap becomes a readable ~10-tile gap between namespace rectangles.
 */
const TILE_SCALE = 42;
const RECTANGLE_PADDING_TILES = 2;
const EMPTY_NAMESPACE_HALF_EXTENT = 2;

function toTile(x: number, y: number): { x: number; y: number } {
  return { x: Math.round(x / TILE_SCALE), y: Math.round(y / TILE_SCALE) };
}

function statusLabel(node: TopologyNode): string {
  if (node.readyEndpoints === null || node.totalEndpoints === null) return "no Endpoints object";
  return `${node.readyEndpoints}/${node.totalEndpoints} endpoints ready`;
}

/**
 * Small, fixed, real-hex rectangle palette (distinct from the endpoint
 * status colors `components/DeckTopology.tsx` uses for node fill, so the
 * two tabs' color vocabularies don't collide) -- cycled by namespace index
 * in the same alphabetical order `lib/topology.ts` already sorts by.
 */
const RECTANGLE_PALETTE = ["#2f4f6b", "#4a3f6b", "#3f6b4f", "#6b4f3f", "#4f3f6b", "#3f5f6b"];
/** Same blue `components/DeckTopology.tsx` uses for its policy ArcLayer. */
const CONNECTOR_COLOR = "#3987e5";

export interface IsoflowConversionResult {
  model: Model;
  /** Real id of the icon actually used for every Service node, and why. */
  serviceIconId: string;
  serviceIconFallback: boolean;
}

/**
 * Builds a real isoflow `Model` from the same inputs `buildTopologySnapshot`
 * takes -- `app/topology/page.tsx` passes the exact same `rows`/`policies`
 * it already fetched via `listServicesWithEndpoints`/`listNetworkPolicies`
 * to both this function and `buildTopologySnapshot`, so no data is fetched
 * or computed twice.
 */
export function buildIsoflowModel(
  rows: Array<{ namespace: string; records: ServiceDiscoveryRecord[] }>,
  policies: IamNetworkPolicy[],
): IsoflowConversionResult {
  const snapshot = buildTopologySnapshot(rows, policies);

  const flattenedIcons: FlattenedIcon[] = flattenCollections([isoflowIsopack, kubernetesIsopack]);
  const kubernetesServiceIcon = flattenedIcons.find((i) => i.id === "k8s-svc");
  const genericFallbackIcon = flattenedIcons.find((i) => i.id === "cube");
  // Every node this converter draws is a real Kubernetes Service, so the
  // real "k8s-svc" icon from @isoflow/isopacks' kubernetes collection is
  // used for all of them. Fallback (never expected to trigger against the
  // installed 0.0.10 kubernetes pack, which does ship "k8s-svc") is the
  // isoflow base pack's generic "cube" node icon.
  const serviceIcon = kubernetesServiceIcon ?? genericFallbackIcon;
  if (!serviceIcon) {
    throw new Error(
      "@isoflow/isopacks shipped neither k8s-svc nor a cube fallback icon -- cannot build a real isoflow model without at least one real icon.",
    );
  }
  const usedIcons: FlattenedIcon[] = [serviceIcon];

  const items: Model["items"] = snapshot.nodes.map((node) => ({
    id: node.id,
    name: node.name,
    description: `${node.namespace} · ${node.dns} · ${statusLabel(node)}`,
    icon: serviceIcon.id,
  }));

  const viewItems: Model["views"][number]["items"] = snapshot.nodes.map((node) => {
    const tile = toTile(node.x, node.y);
    return { id: node.id, tile, labelHeight: 32 };
  });

  const namespacesSorted = [...snapshot.clusters].sort((a, b) => a.namespace.localeCompare(b.namespace));
  const colors: Model["colors"] = [
    { id: "connector-color", value: CONNECTOR_COLOR },
    ...namespacesSorted.map((_, i) => ({
      id: `namespace-color-${i}`,
      value: RECTANGLE_PALETTE[i % RECTANGLE_PALETTE.length],
    })),
  ];

  const rectangles: NonNullable<Model["views"][number]["rectangles"]> = namespacesSorted.map(
    (cluster, i) => {
      const memberTiles = snapshot.nodes
        .filter((n) => n.namespace === cluster.namespace)
        .map((n) => toTile(n.x, n.y));
      const centerTile = toTile(cluster.x, cluster.y);
      const xs = memberTiles.length > 0 ? memberTiles.map((t) => t.x) : [centerTile.x];
      const ys = memberTiles.length > 0 ? memberTiles.map((t) => t.y) : [centerTile.y];
      const halfExtentX = memberTiles.length > 0 ? 0 : EMPTY_NAMESPACE_HALF_EXTENT;
      const halfExtentY = memberTiles.length > 0 ? 0 : EMPTY_NAMESPACE_HALF_EXTENT;
      const minX = Math.min(...xs) - RECTANGLE_PADDING_TILES - halfExtentX;
      const maxX = Math.max(...xs) + RECTANGLE_PADDING_TILES + halfExtentX;
      const minY = Math.min(...ys) - RECTANGLE_PADDING_TILES - halfExtentY;
      const maxY = Math.max(...ys) + RECTANGLE_PADDING_TILES + halfExtentY;
      return {
        id: `ns-rect-${cluster.namespace}`,
        color: `namespace-color-${i}`,
        from: { x: minX, y: minY },
        to: { x: maxX, y: maxY },
      };
    },
  );

  // Real cross-namespace NetworkPolicy ingress-allow edges, anchored by
  // namespace-center tile position -- `TopologyEdge` connects namespace
  // clusters (via `namespaceSelector`), not individual Services, so a
  // tile-anchored connector (rather than an item-anchored one) is the
  // faithful mapping of what this edge actually represents.
  const connectors: NonNullable<Model["views"][number]["connectors"]> = snapshot.edges.map((edge) => {
    const sourceTile = toTile(edge.sourceX, edge.sourceY);
    const targetTile = toTile(edge.targetX, edge.targetY);
    return {
      id: edge.id,
      description: `NetworkPolicy ${edge.policyName}: ${edge.sourceNamespace} → ${edge.targetNamespace}`,
      color: "connector-color",
      width: 2,
      style: "DASHED" as const,
      anchors: [
        { id: `${edge.id}-src`, ref: { tile: sourceTile } },
        { id: `${edge.id}-dst`, ref: { tile: targetTile } },
      ],
    };
  });

  const model: Model = {
    title: "Platform Cluster Topology",
    description:
      "Real Service/NetworkPolicy topology from app/topology/page.tsx, same data as the Spatial (deck.gl) view.",
    items,
    views: [
      {
        id: "cluster-topology-view",
        name: "Cluster Topology",
        items: viewItems,
        rectangles,
        connectors,
      },
    ],
    icons: usedIcons,
    colors,
  };

  return { model, serviceIconId: serviceIcon.id, serviceIconFallback: serviceIcon.id !== "k8s-svc" };
}
