"use client";

import { OrthographicView } from "@deck.gl/core";
import { ArcLayer, ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import DeckGL from "@deck.gl/react";
import { useMemo, useState } from "react";
import type { TopologyEdge, TopologyNamespaceCluster, TopologyNode } from "@/lib/topology";

/**
 * Fixed, reserved status colors (never reused for categorical series) --
 * same four-role vocabulary app/service-discovery/page.tsx's EndpointsBadge
 * already renders as badges (muted/critical/warning/good), reused here as
 * node fill so a Service's dot color always means the same thing across
 * both pages. Dark-surface steps (this app renders `.dark` only), from the
 * dataviz skill's validated status palette -- all clear 3:1 on `#1a1a19`.
 */
const STATUS_COLOR = {
  good: [12, 163, 12, 235] as [number, number, number, number], // #0ca30c -- ready === total > 0
  warning: [250, 178, 25, 235] as [number, number, number, number], // #fab219 -- 0 < ready < total
  critical: [208, 59, 59, 235] as [number, number, number, number], // #d03b3b -- total === 0 or ready === 0
  muted: [137, 135, 129, 200] as [number, number, number, number], // #898781 -- no Endpoints object
};

function statusOf(node: TopologyNode): keyof typeof STATUS_COLOR {
  if (node.readyEndpoints === null || node.totalEndpoints === null) return "muted";
  if (node.totalEndpoints === 0 || node.readyEndpoints === 0) return "critical";
  if (node.readyEndpoints < node.totalEndpoints) return "warning";
  return "good";
}

function statusLabel(node: TopologyNode): string {
  if (node.readyEndpoints === null || node.totalEndpoints === null) return "no Endpoints object";
  return `${node.readyEndpoints}/${node.totalEndpoints} ready`;
}

const ARC_COLOR: [number, number, number, number] = [57, 135, 229, 190]; // categorical slot-1 blue, dark step
const CLUSTER_LABEL_COLOR: [number, number, number, number] = [195, 194, 183, 235]; // secondary ink, dark

const INITIAL_VIEW_STATE = { target: [0, 0, 0] as [number, number, number], zoom: -0.4 };

export interface DeckTopologyProps {
  nodes: TopologyNode[];
  clusters: TopologyNamespaceCluster[];
  edges: TopologyEdge[];
}

export function DeckTopology({ nodes, clusters, edges }: DeckTopologyProps) {
  const [hovered, setHovered] = useState<TopologyNode | null>(null);
  const [selected, setSelected] = useState<TopologyNode | null>(null);
  const active = selected ?? hovered;

  const layers = useMemo(
    () => [
      new ArcLayer<TopologyEdge>({
        id: "policy-arcs",
        data: edges,
        getSourcePosition: (e) => [e.sourceX, e.sourceY],
        getTargetPosition: (e) => [e.targetX, e.targetY],
        getSourceColor: ARC_COLOR,
        getTargetColor: ARC_COLOR,
        getWidth: 2,
        greatCircle: false,
        pickable: true,
      }),
      new ScatterplotLayer<TopologyNode>({
        id: "service-nodes",
        data: nodes,
        getPosition: (n) => [n.x, n.y],
        getRadius: (n) => 7 + Math.min(n.readyEndpoints ?? 0, 6) * 2.4,
        radiusUnits: "pixels",
        getFillColor: (n) => STATUS_COLOR[statusOf(n)],
        getLineColor: (n) => (selected?.id === n.id ? [255, 255, 255, 255] : [10, 10, 10, 160]),
        lineWidthUnits: "pixels",
        getLineWidth: (n) => (selected?.id === n.id ? 3 : 1),
        stroked: true,
        pickable: true,
        onHover: (info) => setHovered((info.object as TopologyNode | undefined) ?? null),
        onClick: (info) => setSelected((info.object as TopologyNode | undefined) ?? null),
      }),
      new TextLayer<TopologyNamespaceCluster>({
        id: "namespace-labels",
        data: clusters,
        getPosition: (c) => [c.x, c.y],
        getText: (c) => `${c.namespace} (${c.serviceCount})`,
        getSize: 13,
        getColor: CLUSTER_LABEL_COLOR,
        getPixelOffset: [0, -108],
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        fontWeight: 600,
        billboard: true,
      }),
    ],
    [nodes, clusters, edges, selected],
  );

  return (
    <div className="relative h-[560px] w-full overflow-hidden rounded-xl border border-border bg-[#111521]">
      <DeckGL
        views={new OrthographicView({ id: "ortho" })}
        initialViewState={INITIAL_VIEW_STATE}
        controller
        layers={layers}
        getCursor={({ isHovering }) => (isHovering ? "pointer" : "grab")}
      />
      {active && (
        <div className="absolute right-3 top-3 w-72 rounded-lg border border-border bg-card/95 p-4 text-sm shadow-lg backdrop-blur">
          <p className="mb-1 text-xs uppercase tracking-wide text-muted-foreground">
            {active.namespace}
          </p>
          <p className="mb-2 font-semibold text-foreground">{active.name}</p>
          <dl className="space-y-1 text-xs">
            <div className="flex justify-between gap-2">
              <dt className="text-muted-foreground">DNS</dt>
              <dd className="break-all text-right text-foreground">{active.dns}</dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className="text-muted-foreground">ClusterIP</dt>
              <dd className="text-foreground">{active.clusterIP ?? "—"}</dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className="text-muted-foreground">Endpoints</dt>
              <dd className="text-foreground">{statusLabel(active)}</dd>
            </div>
          </dl>
          {selected && (
            <button
              type="button"
              className="mt-3 text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
              onClick={() => setSelected(null)}
            >
              clear selection
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default DeckTopology;
