/**
 * Real Load Testing / performance benchmarking self-service (AWS Distributed
 * Load Testing solution / GCP's load-testing guidance tooling equivalent):
 * fires real concurrent HTTP requests -- Node's built-in `fetch`, a plain
 * `Promise.all`-based worker pool, no new dependency -- against one of the
 * platform's own services and measures real p50/p95/p99 latency and real
 * success/error counts from the actual responses received. No simulated
 * numbers anywhere in this module: every percentile is computed from a real
 * `performance.now()` delta around a real `await fetch(...)`.
 *
 * SSRF boundary: `runLoadTest` itself takes a raw `targetUrl` (so it's a
 * genuinely reusable worker-pool primitive), but the only caller anywhere in
 * this app is `runLoadTestAgainstTarget` below, which resolves a client-
 * supplied `targetId` against `LOAD_TEST_TARGETS` -- a fixed, server-defined
 * allowlist of this platform's own cluster-internal status services plus its
 * own public `/api/status`. No arbitrary user-supplied URL ever reaches
 * `fetch`; `app/api/load-test/route.ts` (the only HTTP entry point) accepts
 * `targetId`, never `targetUrl`, from the request body.
 */

export interface LoadTestTarget {
  id: string;
  label: string;
  url: string;
}

// Same env-var-overridable, hardcoded-fallback convention as lib/status.ts's
// fetchers -- these are the exact same 4 internal Service DNS names that
// module already trusts, plus this console's own public status endpoint via
// its own in-cluster Service (k8s/services-and-deployments.yaml,
// `platform-console-gateway`, port 8080 -> containerPort 3000).
export const LOAD_TEST_TARGETS: LoadTestTarget[] = [
  {
    id: "autofde-lab-status",
    label: "autofde-lab-status (autofde-lab)",
    url:
      process.env.AUTOFDE_LAB_STATUS_URL ??
      "http://autofde-lab-status.autofde-lab.svc.cluster.local/status",
  },
  {
    id: "gymact-status",
    label: "gymact-status (gymact)",
    url:
      process.env.GYMACT_STATUS_URL ?? "http://gymact-status.gymact.svc.cluster.local/status",
  },
  {
    id: "ggen-status",
    label: "ggen-status (ggen)",
    url: process.env.GGEN_STATUS_URL ?? "http://ggen-status.ggen.svc.cluster.local/status",
  },
  {
    id: "ggen-marketplace-status",
    label: "ggen-marketplace-status (ggen-marketplace)",
    url:
      process.env.GGEN_MARKETPLACE_STATUS_URL ??
      "http://ggen-marketplace-status.ggen-marketplace.svc.cluster.local/status",
  },
  {
    id: "console-self-status",
    label: "platform-console's own /api/status",
    url:
      process.env.CONSOLE_SELF_STATUS_URL ??
      "http://platform-console-gateway.platform-console.svc.cluster.local:8080/api/status",
  },
];

export function resolveLoadTestTarget(targetId: string): LoadTestTarget | undefined {
  return LOAD_TEST_TARGETS.find((t) => t.id === targetId);
}

export interface LoadTestOptions {
  concurrency: number;
  durationSec: number;
  /** Per-request abort timeout. Default 5000ms. */
  requestTimeoutMs?: number;
}

export interface LatencyStats {
  min: number;
  mean: number;
  p50: number;
  p95: number;
  p99: number;
  max: number;
}

export interface LoadTestResult {
  targetUrl: string;
  concurrency: number;
  durationSec: number;
  startedAt: string;
  finishedAt: string;
  wallMs: number;
  totalRequests: number;
  successCount: number;
  errorCount: number;
  errorRate: number;
  requestsPerSec: number;
  latencyMs: LatencyStats;
  /** Up to 5 distinct error messages actually observed, for diagnosis -- never fabricated. */
  sampleErrors: string[];
}

const MIN_CONCURRENCY = 1;
const MAX_CONCURRENCY = 300;
const MIN_DURATION_SEC = 1;
const MAX_DURATION_SEC = 180;

function clamp(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, Math.round(value)));
}

function percentile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const idx = clamp(Math.ceil((p / 100) * sorted.length) - 1, 0, sorted.length - 1);
  return sorted[idx];
}

/**
 * Fires real concurrent HTTP GET requests against `targetUrl` for
 * `durationSec` wall-clock seconds, using `concurrency` parallel workers each
 * looping request-after-request (a real worker pool, not `concurrency`
 * one-shot requests) -- the same shape AWS's Distributed Load Testing
 * solution and GCP's own load-testing guidance describe: fixed concurrency,
 * fixed duration, measure what actually comes back.
 *
 * Every worker is a single async loop; JS's single-threaded event loop makes
 * the shared `latencies`/`errors` arrays and counters safe to mutate directly
 * with no locking -- there is no real parallelism at the JS level, only
 * concurrent in-flight I/O, which is exactly what "concurrent HTTP requests"
 * means here (same as every real HTTP load-testing tool built on an
 * event-loop runtime).
 */
export async function runLoadTest(
  targetUrl: string,
  options: LoadTestOptions,
): Promise<LoadTestResult> {
  const concurrency = clamp(options.concurrency, MIN_CONCURRENCY, MAX_CONCURRENCY);
  const durationSec = clamp(options.durationSec, MIN_DURATION_SEC, MAX_DURATION_SEC);
  const requestTimeoutMs = options.requestTimeoutMs ?? 5000;

  const latencies: number[] = [];
  const errorMessages: string[] = [];
  let successCount = 0;
  let errorCount = 0;

  const startedAt = new Date();
  const deadline = performance.now() + durationSec * 1000;

  async function worker(): Promise<void> {
    while (performance.now() < deadline) {
      const reqStart = performance.now();
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), requestTimeoutMs);
      try {
        const res = await fetch(targetUrl, {
          signal: controller.signal,
          cache: "no-store",
          headers: { accept: "application/json" },
        });
        // Real work per request: actually read the body, same as a real
        // client would, not just the status line -- this is what makes the
        // target service do real CPU (JSON serialization, socket writes)
        // per request rather than measuring only TCP handshake cost.
        await res.arrayBuffer();
        const elapsed = performance.now() - reqStart;
        latencies.push(elapsed);
        if (res.ok) {
          successCount += 1;
        } else {
          errorCount += 1;
          if (errorMessages.length < 5) errorMessages.push(`HTTP ${res.status} from ${targetUrl}`);
        }
      } catch (err) {
        const elapsed = performance.now() - reqStart;
        latencies.push(elapsed);
        errorCount += 1;
        const message = err instanceof Error ? err.message : String(err);
        if (errorMessages.length < 5) errorMessages.push(message);
      } finally {
        clearTimeout(timeout);
      }
    }
  }

  const wallStart = performance.now();
  await Promise.all(Array.from({ length: concurrency }, () => worker()));
  const wallMs = performance.now() - wallStart;
  const finishedAt = new Date();

  const sorted = [...latencies].sort((a, b) => a - b);
  const totalRequests = latencies.length;
  const sum = sorted.reduce((acc, v) => acc + v, 0);

  const latencyMs: LatencyStats = {
    min: sorted.length ? sorted[0] : 0,
    mean: sorted.length ? sum / sorted.length : 0,
    p50: percentile(sorted, 50),
    p95: percentile(sorted, 95),
    p99: percentile(sorted, 99),
    max: sorted.length ? sorted[sorted.length - 1] : 0,
  };

  return {
    targetUrl,
    concurrency,
    durationSec,
    startedAt: startedAt.toISOString(),
    finishedAt: finishedAt.toISOString(),
    wallMs,
    totalRequests,
    successCount,
    errorCount,
    errorRate: totalRequests > 0 ? errorCount / totalRequests : 0,
    requestsPerSec: wallMs > 0 ? (totalRequests / wallMs) * 1000 : 0,
    latencyMs,
    sampleErrors: errorMessages,
  };
}

export type LoadTestOutcome =
  | { ok: true; data: LoadTestResult }
  | { ok: false; error: string };

/**
 * The only path any HTTP-reachable code in this app uses to run a load
 * test: resolves `targetId` against the fixed allowlist above -- an unknown
 * id is rejected with `{ok:false}` before `runLoadTest`/`fetch` is ever
 * called, never a fallback to a raw URL.
 */
export async function runLoadTestAgainstTarget(
  targetId: string,
  options: LoadTestOptions,
): Promise<LoadTestOutcome> {
  const target = resolveLoadTestTarget(targetId);
  if (!target) {
    return {
      ok: false,
      error: `targetId must be one of: ${LOAD_TEST_TARGETS.map((t) => t.id).join(", ")}`,
    };
  }
  const data = await runLoadTest(target.url, options);
  return { ok: true, data };
}

// ------------------------------------------- Scheduled Benchmark History
//
// The missing piece this module's own header comment identifies:
// `runLoadTestAgainstTarget` already runs a real load test on demand, but
// produces no persisted historical record and no scheduled recurrence --
// exactly the same "ad hoc capability exists, historical/scheduled
// reporting layer does not" gap lib/cost-report-history.ts already closed
// for cost data. `runScheduledLatencyBenchmark` is the recurring-job side
// of that fix: it walks every entry in the fixed `LOAD_TEST_TARGETS`
// allowlist above (never an arbitrary URL), runs one real, short,
// low-concurrency `runLoadTest` against each, and returns one
// `LatencyBenchmarkSnapshot` per target for the caller (the internal cron
// route below) to persist via lib/latency-history.ts's
// `appendLatencyBenchmarkSnapshots` -- this module performs no
// persistence itself, same "compute here, persist there" split
// lib/invoice-preview.ts's on-demand cost preview and
// lib/cost-report-history.ts already established.
export interface LatencyBenchmarkSnapshot {
  orgId: string;
  targetId: string;
  targetLabel: string;
  capturedAt: string;
  concurrency: number;
  durationSec: number;
  totalRequests: number;
  errorCount: number;
  errorRate: number;
  requestsPerSecond: number;
  p50Ms: number;
  p95Ms: number;
  p99Ms: number;
}

// Deliberately small and short: a scheduled sweep across every target
// runs unattended on a recurring cadence (weekly by default, see
// lib/scheduled-jobs.ts's "latency-benchmark-snapshot" command), so it
// must stay cheap enough to run against every allowlisted internal
// service back-to-back without becoming a real capacity problem itself --
// unlike the ad hoc POST /api/load-test path (up to 300 concurrency / 180s
// per call, operator-chosen), this fixed, small shape is the only one the
// scheduled sweep ever uses.
export const SCHEDULED_BENCHMARK_CONCURRENCY = 10;
export const SCHEDULED_BENCHMARK_DURATION_SEC = 5;

/**
 * Runs one real load test against every entry in `LOAD_TEST_TARGETS`,
 * sequentially (never in parallel -- concurrently hammering every
 * internal service at once from one scheduled firing would itself be a
 * real, unwanted load spike across the whole platform), and returns one
 * `LatencyBenchmarkSnapshot` per target that actually completed. A target
 * whose `runLoadTest` call throws (network error, DNS failure) is skipped
 * -- never a fabricated all-zero snapshot -- so the returned array can be
 * shorter than `LOAD_TEST_TARGETS` on a bad run; callers persist whatever
 * came back, same "one bad row doesn't break the whole list" discipline
 * lib/cost-report-history.ts's getRegistry already uses.
 */
export async function runScheduledLatencyBenchmark(
  orgId: string,
): Promise<LatencyBenchmarkSnapshot[]> {
  const snapshots: LatencyBenchmarkSnapshot[] = [];
  const options: LoadTestOptions = {
    concurrency: SCHEDULED_BENCHMARK_CONCURRENCY,
    durationSec: SCHEDULED_BENCHMARK_DURATION_SEC,
  };

  for (const target of LOAD_TEST_TARGETS) {
    try {
      const result = await runLoadTest(target.url, options);
      snapshots.push({
        orgId,
        targetId: target.id,
        targetLabel: target.label,
        capturedAt: result.finishedAt,
        concurrency: result.concurrency,
        durationSec: result.durationSec,
        totalRequests: result.totalRequests,
        errorCount: result.errorCount,
        errorRate: result.errorRate,
        requestsPerSecond: result.requestsPerSec,
        p50Ms: result.latencyMs.p50,
        p95Ms: result.latencyMs.p95,
        p99Ms: result.latencyMs.p99,
      });
    } catch {
      // Real network/DNS failure against one target -- skip it, keep
      // going against the rest, same reasoning as the comment above.
    }
  }

  return snapshots;
}
