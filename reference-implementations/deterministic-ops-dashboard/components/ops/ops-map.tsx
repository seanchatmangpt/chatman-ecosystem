"use client";

import { useMemo } from "react";
import DeckGL from "@deck.gl/react";
import { ArcLayer, ScatterplotLayer } from "@deck.gl/layers";
import type { Color, MapViewState } from "@deck.gl/core";
import { FLOWS, NODES, nodeById, type OpsFlow, type OpsNode } from "@/lib/ops-data";
import { FLOW_SOURCE_RGB, FLOW_TARGET_RGB, STATUS_RGB } from "@/lib/palette";

type OpsArc = OpsFlow & { from: OpsNode; to: OpsNode };

const FLOW_SOURCE_COLOR: Color = [...FLOW_SOURCE_RGB, 190];
const FLOW_TARGET_COLOR: Color = [...FLOW_TARGET_RGB, 190];
const NODE_LINE_COLOR: Color = [10, 10, 10, 200];

// Fixed initial view — no geolocation, no animation loop, so the first paint
// is identical on every load. Deliberately no basemap tile layer: this
// reference implementation makes zero network calls at runtime.
const INITIAL_VIEW_STATE: MapViewState = {
  longitude: 10,
  latitude: 20,
  zoom: 0.75,
  pitch: 0,
  bearing: 0,
};

export function OpsMap() {
  const scatterData = NODES;

  const arcData = useMemo(
    () =>
      FLOWS.map((flow) => {
        const from = nodeById(flow.fromNodeId);
        const to = nodeById(flow.toNodeId);
        return from && to ? { ...flow, from, to } : null;
      }).filter((d): d is NonNullable<typeof d> => d !== null),
    [],
  );

  const layers = [
    new ArcLayer<OpsArc>({
      id: "job-flows",
      data: arcData,
      getSourcePosition: (d) => [d.from.longitude, d.from.latitude],
      getTargetPosition: (d) => [d.to.longitude, d.to.latitude],
      getSourceColor: FLOW_SOURCE_COLOR,
      getTargetColor: FLOW_TARGET_COLOR,
      getWidth: (d) => 1 + d.throughput * 3,
      greatCircle: true,
    }),
    new ScatterplotLayer<OpsNode>({
      id: "ops-nodes",
      data: scatterData,
      getPosition: (d) => [d.longitude, d.latitude],
      getFillColor: (d): Color => [...STATUS_RGB[d.status], 235],
      getRadius: (d) => (d.status === "critical" ? 10 : d.status === "warning" ? 8 : 6),
      radiusUnits: "pixels",
      stroked: true,
      getLineColor: NODE_LINE_COLOR,
      lineWidthUnits: "pixels",
      getLineWidth: 1.5,
      pickable: true,
    }),
  ];

  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg border border-border bg-[#0d1117]">
      <DeckGL
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
        getTooltip={({ object }) =>
          object && "name" in object
            ? {
                text: `${object.name} (${object.region})\nCPU ${object.cpuPct}% · Mem ${object.memPct}%`,
              }
            : null
        }
      />
    </div>
  );
}
