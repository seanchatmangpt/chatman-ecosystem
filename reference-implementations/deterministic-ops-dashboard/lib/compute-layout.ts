import type { Entity } from "./entity-types";

/**
 * Deterministic grid layout for entity graph nodes.
 *
 * Pure function: same input (by structural equality of `entities.map(e =>
 * e.id)`) always produces the exact same output positions. Zero side
 * effects, zero reliance on Math.random(), Date.now(), or any other
 * non-deterministic source — this is the load-bearing property of the whole
 * reference implementation, so keep it that way.
 *
 * Algorithm ("grid" mode, the default and required mode):
 *   1. Sort entities alphabetically by id (stable, independent of input
 *      array order).
 *   2. columns = ceil(sqrt(n)) — a roughly-square grid.
 *   3. Place the i-th sorted entity at grid cell
 *      (i % columns, floor(i / columns)), scaled by SPACING.
 *
 * A future seeded-force-directed mode could be added as `mode: "force"`, but
 * "grid" must remain the default and must remain this simple — no seed, no
 * iteration, no float accumulation that could drift between runs.
 */

export const GRID_SPACING = 200;

export type LayoutMode = "grid";

export interface ComputeLayoutOptions {
  mode?: LayoutMode;
  spacing?: number;
}

export function computeLayout(
  entities: Entity[],
  options: ComputeLayoutOptions = {},
): Record<string, [number, number]> {
  const spacing = options.spacing ?? GRID_SPACING;
  const n = entities.length;
  const columns = Math.max(1, Math.ceil(Math.sqrt(n)));

  const sortedIds = entities.map((e) => e.id).slice().sort();

  const positions: Record<string, [number, number]> = {};
  for (let i = 0; i < sortedIds.length; i++) {
    const col = i % columns;
    const row = Math.floor(i / columns);
    positions[sortedIds[i]] = [col * spacing, row * spacing];
  }

  return positions;
}

/**
 * Memoization note for the next phase (React hook wrapping this function):
 * the memo key MUST be derived from the entity ID list alone, e.g.
 *   const layoutKey = entities.map(e => e.id).join(",");
 *   const layout = useMemo(() => computeLayout(entities), [layoutKey]);
 * Never key on a timestamp, a render count, or the entities array reference
 * itself (a fresh array literal with identical ids is structurally the same
 * input and must hit the memo). Keying on anything else reintroduces the
 * non-determinism this module exists to eliminate.
 */
