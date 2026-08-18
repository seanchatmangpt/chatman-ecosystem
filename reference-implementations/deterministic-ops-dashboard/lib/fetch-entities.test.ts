/**
 * Real tests against the real `fetchEntities`/`parseEntities` implementation
 * — no mocked network layer, no stubbed fixture. The happy path reads the
 * actual bundled fixture file; the failure-path tests feed real,
 * hand-built malformed payloads through the real validator and assert on
 * the real thrown Error message.
 *
 * Run with: node --test lib/fetch-entities.test.ts
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { fetchEntities, parseEntities } from "./fetch-entities.ts";

test("fetchEntities: resolves the real bundled fixture (8-12 plausible entities)", async () => {
  const entities = await fetchEntities();
  assert.ok(entities.length >= 8 && entities.length <= 12, `expected 8-12 entities, got ${entities.length}`);
  for (const e of entities) {
    assert.equal(typeof e.id, "string");
    assert.equal(typeof e.label, "string");
    assert.ok(["healthy", "degraded", "down"].includes(e.status));
    assert.equal(typeof e.metric, "number");
    assert.ok(Array.isArray(e.edges));
  }
  // Real-shaped labels, not "entity-1"/"entity-2" placeholders.
  assert.ok(entities.some((e) => e.label.endsWith("-service") || e.label.endsWith("-api") || e.label.endsWith("-worker") || e.label.endsWith("-gateway")));
});

test("fetchEntities: is deterministic across two real calls", async () => {
  const a = await fetchEntities();
  const b = await fetchEntities();
  assert.strictEqual(JSON.stringify(a), JSON.stringify(b));
});

test("parseEntities: throws a real, descriptive Error on a non-array payload", () => {
  assert.throws(() => parseEntities({ not: "an array" }), /expected an array of entities/);
});

test("parseEntities: throws and names the bad index when a record is missing a required field", () => {
  const malformed = [
    { id: "svc-ok", label: "ok-service", status: "healthy", metric: 10, edges: [] },
    { id: "svc-bad", label: "bad-service", metric: 10, edges: [] }, // missing `status`
  ];
  assert.throws(() => parseEntities(malformed), /1 of 2 record\(s\) failed validation at index 1/);
});

test("parseEntities: throws when status is not one of the real three lifecycle values", () => {
  const malformed = [
    { id: "svc-bad", label: "bad-service", status: "on-fire", metric: 10, edges: [] },
  ];
  assert.throws(() => parseEntities(malformed), /failed validation/);
});

test("parseEntities: throws when an edge is malformed (weight not a number)", () => {
  const malformed = [
    {
      id: "svc-bad",
      label: "bad-service",
      status: "healthy",
      metric: 10,
      edges: [{ targetId: "svc-ok", weight: "high" }],
    },
  ];
  assert.throws(() => parseEntities(malformed), /failed validation/);
});

test("parseEntities: accepts a well-formed minimal payload", () => {
  const good = [{ id: "svc-x", label: "x-service", status: "healthy", metric: 1, edges: [] }];
  assert.deepStrictEqual(parseEntities(good), good);
});
