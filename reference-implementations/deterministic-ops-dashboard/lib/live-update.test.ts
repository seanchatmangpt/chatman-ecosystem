/**
 * Proves the data contract that requirement #10 (live updates without
 * repositioning) depends on: for a fixed entity-*id* set, `computeLayout`'s
 * output is byte-identical across two "poll ticks" even when every entity's
 * metric/status changes — and, symmetrically, that the metric/status-driven
 * visual encodings (node radius, fill color) DO change when the underlying
 * data changes.
 *
 * This is what makes it correct for `OpsDashboardCanvas` to memoize
 * `computeLayout(entities)` on the id-set alone —
 *   const layoutKey = entities.map(e => e.id).join(",");
 *   const layout = useMemo(() => computeLayout(entities), [layoutKey]);
 * (see `lib/compute-layout.ts`'s memoization note, and the real usage in
 * `components/OpsDashboardCanvas.tsx`) — a metric/status-only update on tick
 * 2 can never need to recompute node positions, because the underlying
 * function provably ignores those fields.
 *
 * This file does not exercise React's `useMemo` bailout mechanism itself —
 * no DOM/test-renderer dependency exists in this project, and Chicago-style
 * testing discipline prefers proving the real underlying data contract over
 * adding a mocking/rendering harness just to assert React internals. What is
 * proven here — the pure function `computeLayout` and the pure encoding
 * functions in `lib/visual-encoding.ts`, called directly, no test doubles —
 * is the substantive claim: positions are stable, encodings are not.
 *
 * Run with: node --test lib/live-update.test.ts
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { computeLayout } from "./compute-layout.ts";
import type { Entity } from "./entity-types.ts";
import { nodeRadiusPx, STATUS_COLOR } from "./visual-encoding.ts";

const TICK_1: Entity[] = [
  { id: "svc-a", label: "a", status: "healthy", metric: 20, edges: [] },
  { id: "svc-b", label: "b", status: "degraded", metric: 40, edges: [] },
  { id: "svc-c", label: "c", status: "down", metric: 10, edges: [] },
];

// Same id set as TICK_1, but every metric and every status changed — this is
// exactly the shape of an ordinary poll tick against a live backend.
const TICK_2: Entity[] = [
  { id: "svc-a", label: "a", status: "down", metric: 91, edges: [] },
  { id: "svc-b", label: "b", status: "healthy", metric: 5, edges: [] },
  { id: "svc-c", label: "c", status: "degraded", metric: 77, edges: [] },
];

test("live update: sanity — tick 2 really did change every metric and status (test isn't vacuous)", () => {
  for (let i = 0; i < TICK_1.length; i++) {
    assert.notStrictEqual(TICK_1[i].metric, TICK_2[i].metric);
    assert.notStrictEqual(TICK_1[i].status, TICK_2[i].status);
  }
});

test("live update: same id set -> byte-identical layout across ticks despite metric/status churn", () => {
  const layoutKey1 = TICK_1.map((e) => e.id).join(",");
  const layoutKey2 = TICK_2.map((e) => e.id).join(",");
  assert.strictEqual(layoutKey1, layoutKey2, "the memo key OpsDashboardCanvas actually uses is unchanged");

  const layout1 = computeLayout(TICK_1);
  const layout2 = computeLayout(TICK_2);
  assert.deepStrictEqual(layout1, layout2);
  assert.strictEqual(JSON.stringify(layout1), JSON.stringify(layout2));

  for (const entity of TICK_1) {
    assert.deepStrictEqual(layout1[entity.id], layout2[entity.id]);
  }
});

test("live update: metric-driven radius DOES differ across ticks for every entity", () => {
  for (let i = 0; i < TICK_1.length; i++) {
    const r1 = nodeRadiusPx(TICK_1[i].metric);
    const r2 = nodeRadiusPx(TICK_2[i].metric);
    assert.notStrictEqual(r1, r2, `radius must track metric for ${TICK_1[i].id}`);
  }
});

test("live update: status-driven fill color DOES differ across ticks for every entity", () => {
  for (let i = 0; i < TICK_1.length; i++) {
    const c1 = STATUS_COLOR[TICK_1[i].status];
    const c2 = STATUS_COLOR[TICK_2[i].status];
    assert.notDeepStrictEqual(c1, c2, `fill color must track status for ${TICK_1[i].id}`);
  }
});

test("live update: an id-set change (real add/remove) DOES change the layout — memoization is keyed correctly, not just always-stable", () => {
  const TICK_3: Entity[] = [...TICK_1, { id: "svc-d", label: "d", status: "healthy", metric: 15, edges: [] }];
  const layoutKey1 = TICK_1.map((e) => e.id).join(",");
  const layoutKey3 = TICK_3.map((e) => e.id).join(",");
  assert.notStrictEqual(layoutKey1, layoutKey3);

  const layout1 = computeLayout(TICK_1);
  const layout3 = computeLayout(TICK_3);
  assert.notStrictEqual(JSON.stringify(layout1), JSON.stringify(layout3));
});
