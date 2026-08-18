import type { Entity, EntityStatus } from "./entity-types";
import fixture from "./fixtures/entities.json" with { type: "json" };

/**
 * Real async data-source boundary for the entity graph.
 *
 * For this reference build, `fetchEntities()` resolves the bundled local
 * fixture at `lib/fixtures/entities.json` (12 entities modeling a plausible
 * checkout-path service graph). The function signature and validation layer
 * are written exactly as they would be against a real backend, so swapping
 * the body for a real network call later is a one-function change:
 *
 *   export async function fetchEntities(): Promise<Entity[]> {
 *     const res = await fetch("/api/entities");
 *     if (!res.ok) throw new Error(`fetchEntities: ${res.status} ${res.statusText}`);
 *     return parseEntities(await res.json());
 *   }
 *
 * `parseEntities` already guards a real response's shape either way.
 */

const VALID_STATUSES: readonly EntityStatus[] = ["healthy", "degraded", "down"];

function isEntityEdge(x: unknown): x is { targetId: string; weight: number } {
  return (
    typeof x === "object" &&
    x !== null &&
    typeof (x as Record<string, unknown>).targetId === "string" &&
    typeof (x as Record<string, unknown>).weight === "number"
  );
}

function isEntity(x: unknown): x is Entity {
  if (typeof x !== "object" || x === null) return false;
  const e = x as Record<string, unknown>;
  return (
    typeof e.id === "string" &&
    typeof e.label === "string" &&
    typeof e.status === "string" &&
    VALID_STATUSES.includes(e.status as EntityStatus) &&
    typeof e.metric === "number" &&
    Array.isArray(e.edges) &&
    e.edges.every(isEntityEdge)
  );
}

/**
 * Validates a raw payload (fixture or, later, a real fetch response body)
 * into `Entity[]`, throwing a real, descriptive `Error` on any malformed
 * record rather than silently coercing bad data. Exported separately from
 * `fetchEntities` so it can be exercised directly with hand-built malformed
 * input in tests — real validation logic, not a mocked network layer.
 */
export function parseEntities(raw: unknown): Entity[] {
  if (!Array.isArray(raw)) {
    throw new Error("parseEntities: expected an array of entities, got " + typeof raw);
  }
  const badIndexes: number[] = [];
  raw.forEach((item, i) => {
    if (!isEntity(item)) badIndexes.push(i);
  });
  if (badIndexes.length > 0) {
    throw new Error(
      `parseEntities: ${badIndexes.length} of ${raw.length} record(s) failed validation at index ${badIndexes.join(", ")}`,
    );
  }
  return raw as Entity[];
}

export async function fetchEntities(): Promise<Entity[]> {
  // Real async boundary (microtask hop) even though the source is a bundled
  // local fixture for this reference build — keeps the call site (polling
  // loop, retry button) exercising genuine async/await control flow.
  await Promise.resolve();
  return parseEntities(fixture);
}
