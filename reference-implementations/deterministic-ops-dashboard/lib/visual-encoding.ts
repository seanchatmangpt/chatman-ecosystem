import type { EntityStatus } from "./entity-types";
import { FLOW_SOURCE_RGB, FLOW_TARGET_RGB, STATUS_RGB } from "./palette.ts";

/**
 * Framework-free visual-encoding formulas shared by `OpsDashboardCanvas`
 * (deck.gl layers) and by node tests (`lib/live-update.test.ts`). Pulled out
 * of the canvas component specifically so these formulas — which are pure
 * functions of `Entity` fields, never of layout/position — can be exercised
 * by `node --test` without importing deck.gl/React (deck.gl touches
 * `window`/WebGL at module init and must never load outside a browser).
 */

export { FLOW_SOURCE_RGB, FLOW_TARGET_RGB };

/**
 * Fixed, documented status -> RGBA lookup for node fill color. Built from
 * the same validated `STATUS_RGB` palette the rest of the app uses (see
 * `lib/palette.ts`), just re-keyed onto the entity graph's real
 * `EntityStatus` lifecycle instead of the ops-map's `good/warning/critical`
 * labels. A plain object literal, never `d3.scaleOrdinal` or any other
 * unseeded/order-dependent color assignment.
 */
export const STATUS_COLOR: Record<EntityStatus, [number, number, number, number]> = {
  healthy: [...STATUS_RGB.good, 235],
  degraded: [...STATUS_RGB.warning, 235],
  down: [...STATUS_RGB.critical, 235],
};

/**
 * Node radius formula: sqrt scale of `entity.metric`, not linear.
 * `entity.metric` ranges roughly 14..88 across the fixture graph
 * (sqrt(14) ≈ 3.74, sqrt(88) ≈ 9.38), so the resulting radius range is
 * RADIUS_MIN + RADIUS_SCALE * sqrt(metric) ≈ 12.7..22.9 px — big enough to
 * read at a glance, without a high-traffic node dwarfing a low-traffic one
 * the way a linear scale would.
 */
export const RADIUS_MIN_PX = 6;
export const RADIUS_SCALE_PX = 1.8;

export function nodeRadiusPx(metric: number): number {
  return RADIUS_MIN_PX + RADIUS_SCALE_PX * Math.sqrt(metric);
}

/**
 * Arc width/opacity formula: both driven linearly by the edge's real
 * `weight` (0..1 relative traffic share), never a constant.
 *   width (px)     = ARC_WIDTH_MIN_PX + weight * ARC_WIDTH_SCALE_PX  ->  1..8 px
 *   alpha (0-255)  = ARC_ALPHA_MIN + weight * ARC_ALPHA_SCALE        -> 60..210
 * A higher-traffic call relationship reads as a thicker, more opaque arc.
 */
export const ARC_WIDTH_MIN_PX = 1;
export const ARC_WIDTH_SCALE_PX = 7;
export const ARC_ALPHA_MIN = 60;
export const ARC_ALPHA_SCALE = 150;

export function arcWidthPx(weight: number): number {
  return ARC_WIDTH_MIN_PX + weight * ARC_WIDTH_SCALE_PX;
}

export function arcColor(
  rgb: readonly [number, number, number],
  weight: number,
): [number, number, number, number] {
  return [rgb[0], rgb[1], rgb[2], Math.round(ARC_ALPHA_MIN + weight * ARC_ALPHA_SCALE)];
}
