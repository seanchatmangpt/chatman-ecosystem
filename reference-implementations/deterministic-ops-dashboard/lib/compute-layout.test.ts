/**
 * Real determinism proof for computeLayout — no float-tolerance fuzz, exact
 * deep-equal comparisons only. Run with:
 *
 *   node --test lib/compute-layout.test.ts
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { computeLayout } from "./compute-layout.ts";
import { SERVICE_ENTITIES, type Entity } from "./entity-types.ts";

test("computeLayout: repeatable — identical array reference twice", () => {
  const a = computeLayout(SERVICE_ENTITIES);
  const b = computeLayout(SERVICE_ENTITIES);
  assert.deepStrictEqual(a, b);
  assert.strictEqual(JSON.stringify(a), JSON.stringify(b));
});

test("computeLayout: repeatable — two structurally-identical but distinct arrays", () => {
  const listA: Entity[] = SERVICE_ENTITIES.map((e) => ({ ...e, edges: [...e.edges] }));
  const listB: Entity[] = SERVICE_ENTITIES.map((e) => ({ ...e, edges: [...e.edges] }));
  assert.notStrictEqual(listA, listB); // distinct array objects
  assert.notStrictEqual(listA[0], listB[0]); // distinct element objects too

  const a = computeLayout(listA);
  const b = computeLayout(listB);
  assert.deepStrictEqual(a, b);
  assert.strictEqual(JSON.stringify(a), JSON.stringify(b));
});

test("computeLayout: input-sensitive — a different entity list yields different output", () => {
  const original = computeLayout(SERVICE_ENTITIES);

  const differentList: Entity[] = [
    { id: "svc-zzz-new", label: "zzz-new-service", status: "healthy", metric: 5, edges: [] },
    ...SERVICE_ENTITIES,
  ];
  const different = computeLayout(differentList);

  assert.notStrictEqual(
    JSON.stringify(original),
    JSON.stringify(different),
    "layout must change when the entity list changes — otherwise it's a constant, not a function of input",
  );

  // The new id must actually appear with a real computed position.
  assert.ok(different["svc-zzz-new"] !== undefined);
  assert.strictEqual(Object.keys(different).length, SERVICE_ENTITIES.length + 1);
});

test("computeLayout: no hidden state — re-running with the ORIGINAL list a third time reproduces the original positions", () => {
  const run1 = computeLayout(SERVICE_ENTITIES);

  const differentList: Entity[] = [
    { id: "svc-zzz-new", label: "zzz-new-service", status: "healthy", metric: 5, edges: [] },
    ...SERVICE_ENTITIES,
  ];
  computeLayout(differentList); // run against different input in between

  const run3 = computeLayout(SERVICE_ENTITIES); // back to the original list

  assert.deepStrictEqual(run1, run3);
  assert.strictEqual(JSON.stringify(run1), JSON.stringify(run3));
});

test("computeLayout: grid geometry sanity — sorted alphabetically, ceil(sqrt(n)) columns, fixed spacing", () => {
  const entities: Entity[] = [
    { id: "c", label: "c", status: "healthy", metric: 1, edges: [] },
    { id: "a", label: "a", status: "healthy", metric: 1, edges: [] },
    { id: "b", label: "b", status: "healthy", metric: 1, edges: [] },
    { id: "d", label: "d", status: "healthy", metric: 1, edges: [] },
  ];
  // n=4 -> columns = ceil(sqrt(4)) = 2
  const layout = computeLayout(entities);
  assert.deepStrictEqual(layout, {
    a: [0, 0],
    b: [200, 0],
    c: [0, 200],
    d: [200, 200],
  });
});
