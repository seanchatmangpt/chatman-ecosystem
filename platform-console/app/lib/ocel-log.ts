/**
 * Server-side proxy to the OCEL accumulator's status endpoint (Plan step C,
 * `ggen-marketplace/packs/otel-weaver-ocel-pack/generated/src/bin/ocel_accumulator.rs`
 * per `~/.claude/plans/eager-forging-sparrow.md`). Same fail-closed convention
 * as lib/tracing.ts and lib/prometheus.ts: on any error this returns
 * { ok: false }, never a fabricated event count.
 *
 * Step C is now real and deployed (Deployment/Service `ocel-accumulator` in
 * `istio-system`, port 4900 -- confirmed live, real growing eventCount).
 * `/discovery` is being added to the accumulator itself (a real subprocess
 * bridge to wasm4pm-cli, castle's pattern) -- until it lands, this proxy
 * correctly fails closed on that one call rather than fabricating a result.
 */

export type OcelLogResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

export interface OcelAccumulatorStatus {
  eventCount: number;
  objectCount: number;
  lastUpdated: string; // ISO
}

export interface OcelDiscoveryResult {
  algorithm: string;
  raw: unknown;
}

const FETCH_TIMEOUT_MS = 5000;

function baseUrl(): string {
  return (
    process.env.OCEL_ACCUMULATOR_URL ??
    "http://ocel-accumulator.istio-system.svc.cluster.local:4900"
  );
}

async function accumulatorFetch<T>(path: string): Promise<OcelLogResult<T>> {
  const url = `${baseUrl()}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    const body = (await res.json().catch(() => null)) as T | null;
    if (!res.ok || !body) {
      return { ok: false, error: `HTTP ${res.status} from ${url}` };
    }
    return { ok: true, data: body };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}

/** The accumulator's own {eventCount, objectCount, lastUpdated} status endpoint. */
export async function getOcelAccumulatorStatus(): Promise<
  OcelLogResult<OcelAccumulatorStatus>
> {
  return accumulatorFetch<OcelAccumulatorStatus>("/status");
}

/**
 * One real discovery run against the accumulator's current OCEL log, shelled
 * out server-side to wasm4pm-cli's `mining`/`ocdfg_bridge` -- never invoked
 * from this proxy itself (that subprocess call belongs in the accumulator's
 * own discovery endpoint per castle's subprocess-bridge pattern, not in the
 * Next.js server). This just relays that endpoint's real, possibly sparse
 * result -- it does not densify or synthesize anything.
 */
export async function getOcelDiscoveryResult(): Promise<
  OcelLogResult<OcelDiscoveryResult>
> {
  return accumulatorFetch<OcelDiscoveryResult>("/discovery");
}
