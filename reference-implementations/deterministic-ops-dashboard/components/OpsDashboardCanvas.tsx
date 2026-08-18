"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import DeckGL from "@deck.gl/react";
import { OrthographicView } from "@deck.gl/core";
import type { Color, OrthographicViewState, PickingInfo } from "@deck.gl/core";
import { ArcLayer, ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import { computeLayout } from "@/lib/compute-layout";
import type { Entity } from "@/lib/entity-types";
import {
  arcColor,
  arcWidthPx,
  FLOW_SOURCE_RGB,
  FLOW_TARGET_RGB,
  nodeRadiusPx,
  STATUS_COLOR,
} from "@/lib/visual-encoding";

const NODE_LINE_COLOR: Color = [10, 10, 10, 200];
const SELECTED_LINE_COLOR: Color = [255, 255, 255, 235];

// Text offset from the node center, in *screen pixels*: (radius + 4) right,
// 8 down (roughly level with the node, clear of its edge). Deck.gl positions
// TextLayer data in world space, and world space is scaled by 2**zoom before
// it reaches the screen (OrthographicView: zoom 0 = 1 world unit = 1 px,
// +1 zoom doubles screen size). So a *constant* world-space offset would
// drift further from the node, in screen pixels, as the user zooms in. To
// keep the label pinned at the same apparent (radius+4, 8) px offset at any
// zoom level, the pixel offset here is divided by the current scale factor
// (2**zoom) before being added to the node's world position.
const TEXT_OFFSET_X_PX = 4; // added on top of the per-node radius
const TEXT_OFFSET_Y_PX = 8;

type LayoutMap = Record<string, [number, number]>;

interface Bounds {
  minX: number;
  maxX: number;
  minY: number;
  maxY: number;
}

function boundsOf(layout: LayoutMap): Bounds {
  const positions = Object.values(layout);
  const xs = positions.map((p) => p[0]);
  const ys = positions.map((p) => p[1]);
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
  };
}

// Extra world-space margin around the tightest bounding box, as a fraction
// of the fitted scale, so nodes at the edge (plus their radius/labels)
// aren't clipped by the viewport edge.
const FIT_PADDING_FACTOR = 0.8; // fit to 80% of the viewport, 10% margin per side

function fitViewState(bounds: Bounds, viewportWidth: number, viewportHeight: number): OrthographicViewState {
  const spanX = Math.max(bounds.maxX - bounds.minX, 1);
  const spanY = Math.max(bounds.maxY - bounds.minY, 1);
  const target: [number, number] = [(bounds.minX + bounds.maxX) / 2, (bounds.minY + bounds.maxY) / 2];

  // zoom: 0 => 1 world unit = 1 screen px; +1 doubles the on-screen scale.
  // Solve for the zoom that fits the real content span into the real
  // measured viewport, then back off by FIT_PADDING_FACTOR for margin.
  const scaleToFitX = viewportWidth / spanX;
  const scaleToFitY = viewportHeight / spanY;
  const scale = Math.min(scaleToFitX, scaleToFitY) * FIT_PADDING_FACTOR;
  const zoom = Math.log2(scale);

  return { target, zoom };
}

/** Reads a CSS color (e.g. an oklch() custom property) and rasterizes it
 * through a 1x1 canvas to get the real sRGB bytes the browser would paint —
 * this is how we get the theme's actual `--foreground` value as RGB without
 * hand-maintaining a hex duplicate of it (canvas `fillStyle` accepts any
 * valid CSS color, including oklch()/color-mix(), and always resolves to
 * sRGB when read back via getImageData). Falls back to opaque white only if
 * canvas 2D is unavailable (non-browser environment). */
function cssColorToRgb(cssColor: string): [number, number, number] {
  if (typeof document === "undefined") return [255, 255, 255];
  const canvas = document.createElement("canvas");
  canvas.width = 1;
  canvas.height = 1;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  if (!ctx) return [255, 255, 255];
  ctx.fillStyle = cssColor;
  ctx.fillRect(0, 0, 1, 1);
  const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
  return [r, g, b];
}

export interface OpsDashboardCanvasProps {
  /** Live entity list — new data every poll tick, but the same `id` set on
   * an ordinary metric/status-only update (see `lib/live-update.test.ts`). */
  entities: Entity[];
  /** Currently selected entity id, owned by the parent dashboard so deck.gl
   * clicks, table row clicks, and the command palette all drive the same
   * selection state. */
  selectedId: string | null;
  onSelect: (id: string | null) => void;
}

export function OpsDashboardCanvas({ entities, selectedId, onSelect }: OpsDashboardCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [viewportSize, setViewportSize] = useState<{ width: number; height: number } | null>(null);
  const [hovered, setHovered] = useState<Entity | null>(null);

  // Measure the real container box (no assumed/hardcoded canvas size) and
  // keep it live via ResizeObserver so a window resize refits the view.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) setViewportSize({ width, height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Memoize computeLayout on the entity-*id-set* only (per the memoization
  // note in lib/compute-layout.ts) — a poll tick that changes metric/status
  // but keeps the same ids must NOT recompute positions. Real behavior
  // proven at the data-contract level in lib/live-update.test.ts.
  const layoutKey = useMemo(() => entities.map((e) => e.id).join(","), [entities]);
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: key on layoutKey, not the entities array reference
  const layout = useMemo(() => computeLayout(entities), [layoutKey]);

  const textColor = useMemo<[number, number, number, number]>(() => {
    if (typeof window === "undefined") return [245, 245, 245, 255];
    const fg = getComputedStyle(document.documentElement).getPropertyValue("--foreground").trim();
    const [r, g, b] = cssColorToRgb(fg || "white");
    return [r, g, b, 255];
  }, []);

  const initialViewState = useMemo<OrthographicViewState | null>(() => {
    if (!viewportSize) return null;
    const bounds = boundsOf(layout);
    return fitViewState(bounds, viewportSize.width, viewportSize.height);
  }, [layout, viewportSize]);

  const arcData = useMemo(() => {
    const byId = new Map(entities.map((e) => [e.id, e]));
    return entities.flatMap((entity) =>
      entity.edges
        .filter((edge) => byId.has(edge.targetId) && layout[entity.id] && layout[edge.targetId])
        .map((edge) => ({
          sourceId: entity.id,
          targetId: edge.targetId,
          weight: edge.weight,
        })),
    );
  }, [entities, layout]);

  const layers = useMemo(() => {
    if (!initialViewState) return [];
    const zoom = typeof initialViewState.zoom === "number" ? initialViewState.zoom : 0;
    const pixelToWorld = 1 / 2 ** zoom;

    return [
      new ArcLayer<(typeof arcData)[number]>({
        id: "entity-edges",
        data: arcData,
        getSourcePosition: (d) => layout[d.sourceId],
        getTargetPosition: (d) => layout[d.targetId],
        getWidth: (d) => arcWidthPx(d.weight),
        widthUnits: "pixels",
        getSourceColor: (d) => arcColor(FLOW_SOURCE_RGB, d.weight),
        getTargetColor: (d) => arcColor(FLOW_TARGET_RGB, d.weight),
      }),
      new ScatterplotLayer<Entity>({
        id: "entity-nodes",
        data: entities,
        getPosition: (d) => layout[d.id],
        getRadius: (d) => nodeRadiusPx(d.metric),
        radiusUnits: "pixels",
        getFillColor: (d) => STATUS_COLOR[d.status],
        stroked: true,
        getLineColor: (d) => (d.id === selectedId ? SELECTED_LINE_COLOR : NODE_LINE_COLOR),
        lineWidthUnits: "pixels",
        getLineWidth: (d) => (d.id === selectedId ? 3 : 1.5),
        pickable: true,
        updateTriggers: {
          getLineColor: [selectedId],
          getLineWidth: [selectedId],
        },
      }),
      new TextLayer<Entity>({
        id: "entity-labels",
        data: entities,
        getText: (d) => d.label,
        getPosition: (d) => {
          const [x, y] = layout[d.id];
          const dx = (nodeRadiusPx(d.metric) + TEXT_OFFSET_X_PX) * pixelToWorld;
          const dy = TEXT_OFFSET_Y_PX * pixelToWorld;
          return [x + dx, y + dy];
        },
        getSize: 12,
        sizeUnits: "pixels",
        sizeMinPixels: 10,
        sizeMaxPixels: 16,
        getColor: textColor,
        getTextAnchor: "start",
        getAlignmentBaseline: "center",
      }),
    ];
  }, [arcData, entities, initialViewState, layout, selectedId, textColor]);

  const handleHover = (info: PickingInfo) => {
    setHovered((info.object as Entity | undefined) ?? null);
  };

  const handleClick = (info: PickingInfo) => {
    const clicked = info.object as Entity | undefined;
    onSelect(clicked?.id ?? null);
  };

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden rounded-lg border border-border bg-[#0d1117]">
      {initialViewState && (
        <DeckGL
          views={new OrthographicView({ id: "ops-graph" })}
          initialViewState={initialViewState}
          controller={true}
          layers={layers}
          onHover={handleHover}
          onClick={handleClick}
          getTooltip={() =>
            hovered
              ? { text: `${hovered.label}\n${hovered.status} · metric ${hovered.metric}` }
              : null
          }
        />
      )}
    </div>
  );
}
