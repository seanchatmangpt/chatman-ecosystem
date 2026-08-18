/**
 * Fixed data-viz palette (validated, mode-invariant status colors; dark-mode
 * categorical steps for the deck.gl layers, since this app defaults to dark).
 * See the `dataviz` skill's `references/palette.md` for provenance and the
 * CVD/contrast validation this ordering passed.
 */

export const STATUS_HEX = {
  good: "#0ca30c",
  warning: "#fab219",
  critical: "#d03b3b",
} as const;

// Categorical slot 1 (blue) and slot 3 (aqua), dark-mode steps.
export const FLOW_SOURCE_HEX = "#3987e5";
export const FLOW_TARGET_HEX = "#199e70";

export function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "");
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  return [r, g, b];
}

export const STATUS_RGB = {
  good: hexToRgb(STATUS_HEX.good),
  warning: hexToRgb(STATUS_HEX.warning),
  critical: hexToRgb(STATUS_HEX.critical),
} as const;

export const FLOW_SOURCE_RGB = hexToRgb(FLOW_SOURCE_HEX);
export const FLOW_TARGET_RGB = hexToRgb(FLOW_TARGET_HEX);
