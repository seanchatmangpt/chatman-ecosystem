/**
 * Server-side proxy to the OCEL accumulator's status endpoint (Plan step C,
 * `ggen-marketplace/packs/otel-weaver-ocel-pack/generated/src/bin/ocel_accumulator.rs`
 * per `~/.claude/plans/eager-forging-sparrow.md`). Same fail-closed convention
 * as lib/tracing.ts and lib/prometheus.ts: on any error this returns
 * { ok: false }, never a fabricated event count.
 *
 * Step C is now real and deployed (Deployment/Service `ocel-accumulator` in
 * `istio-system`, port 4900 -- confirmed live). NOTE (2026-08-19): eventCount
 * is not currently growing in steady state -- this is real idleness, not a
 * bug: the Collector has received zero spans since its last restart (no
 * `otelcol_receiver_accepted_spans`/`otelcol_exporter_sent_spans` series at
 * all on its own /metrics), so the on-disk log's 14 events are a one-time
 * seed/manual-test batch, not continuous traffic. See
 * `k8s/weaver-livecheck.yaml` for the disclosed, still-open, out-of-scope
 * limitation (no istio-cni for the gateway/prober) this traces back to.
 * `/discovery` is now live and confirmed working (returns a real mined
 * OC-DFG from the accumulator's stored events) -- this proxy relays it
 * as-is, still failing closed on any HTTP/parse error rather than
 * fabricating a result.
 *
 * KNOWN GAP (2026-08-19): the accumulator's `/status` always serializes
 * `lastUpdated: null`, even though real events exist with a real on-disk
 * write time. This is a real bug in the accumulator binary's status
 * handler, but its cited source --
 * `ggen-marketplace/packs/otel-weaver-ocel-pack/generated/src/bin/
 * ocel_accumulator.rs` -- does not exist anywhere in this checkout (nor
 * does the `otel_span_to_ocel_evidence` transformer it's supposed to call);
 * only the compiled binary is running in the live pod. Fixing this in
 * source requires first recovering or fully re-authoring that pack, which
 * is out of scope for this pass -- tracked here as a named, confirmed gap,
 * not silently patched around.
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

// ---------------------------------------------------------------------------
// Local OC-DFG discovery via a real wasm4pm-cli subprocess (`wpm`)
// ---------------------------------------------------------------------------
//
// Deliberately separate from `getOcelDiscoveryResult` above and from
// `accumulatorFetch`: this does not call the deployed `ocel-accumulator`
// Service at all. It shells out, server-side, to a real `wasm4pm-cli`
// binary (`wpm mining discover --algo ocdfg -o <file>`, real subcommand
// confirmed live at crates/wasm4pm-cli/src/commands/mining.rs and
// crates/wasm4pm-cli/src/commands/ocdfg_bridge.rs in the wasm4pm repo,
// which wraps `wasm4pm::advanced::ocdfg::OCDFG::discover`) against an
// `OcelLog` supplied directly by the caller, and parses the real OCDFG
// JSON the CLI writes back out.
//
// This is a second, independently-comparable discovery path -- it exists
// so platform-console has one real, in-repo wasm4pm consumer, distinct
// from (and not a replacement for) the accumulator proxy above. It follows
// the same subprocess convention as `lib/custom-domains.ts`'s
// `generateSelfSignedCertificate` (execFileSync against a real CLI, a
// mkdtemp scratch dir, explicit input/output file paths, a bounded
// timeout, fail-closed on any error) -- not a second, driftable pattern.
//
// `wpm mining discover` only reads a `.json` FILE PATH (no stdin support,
// confirmed by reading crates/wasm4pm-cli/src/commands/mining.rs's
// `load_ocel`), so the input log is written to a temp file rather than
// piped. The CLI's `ocdfg` branch had no `-o`/JSON output path before this
// integration (it only printed a colored terminal table); JSON output
// support was added to it (crates/wasm4pm-cli/src/commands/mining.rs) as
// a real, additive part of this change so it can be consumed
// programmatically here.

import { execFileSync } from "node:child_process";
import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

/** Minimal OCEL 2.0 log shape accepted by wasm4pm's tolerant OCEL parser. */
export interface OcelLog {
  eventTypes: string[];
  objectTypes: string[];
  events: Array<{
    id: string;
    type: string;
    time: string;
    attributes: Record<string, unknown>;
    relationships: Array<{ objectId: string; qualifier: string }>;
  }>;
  objects: Array<{
    id: string;
    type: string;
    attributes: Record<string, unknown>;
  }>;
}

export interface OcDfgEdge {
  from: string;
  to: string;
  frequency: number;
}

export interface OcDfgNode {
  id: string;
  label: string;
  frequency: number;
}

export interface DFG {
  nodes: OcDfgNode[];
  edges: OcDfgEdge[];
  start_activities: Record<string, number>;
  end_activities: Record<string, number>;
}

/** The real `wasm4pm::advanced::ocdfg::OCDFG` struct, one DFG per object type. */
export interface OCDFG {
  dfgs: Record<string, DFG>;
}

const WPM_TIMEOUT_MS = 15_000;

function wpmBinaryPath(): string {
  return process.env.WPM_BIN_PATH ?? "wpm";
}

/**
 * Discover an Object-Centric Directly-Follows Graph from `log` by shelling
 * out, server-side, to a real `wasm4pm-cli` (`wpm`) subprocess. Returns the
 * real parsed `OCDFG` on success; throws on any subprocess/parse failure
 * (fail-closed, same convention as `accumulatorFetch` above -- callers
 * decide how to surface the error, this function never fabricates a
 * result).
 */
export function discoverOcDfgLocal(log: OcelLog): OCDFG {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "ocdfg-discover-"));
  try {
    const inputPath = path.join(dir, "input.json");
    const outputPath = path.join(dir, "output.json");
    fs.writeFileSync(inputPath, JSON.stringify(log));

    execFileSync(
      wpmBinaryPath(),
      ["mining", "discover", inputPath, "--algo", "ocdfg", "-o", outputPath],
      { stdio: ["ignore", "pipe", "pipe"], timeout: WPM_TIMEOUT_MS },
    );

    const raw = fs.readFileSync(outputPath, "utf8");
    const parsed = JSON.parse(raw) as OCDFG;
    if (!parsed || typeof parsed.dfgs !== "object") {
      throw new Error("wpm mining discover --algo ocdfg produced no dfgs field");
    }
    return parsed;
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}
