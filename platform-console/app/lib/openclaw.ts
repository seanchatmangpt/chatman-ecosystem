/**
 * Real client for the autofde-lab OpenClaw MCP bridge sidecar
 * (services/autofde-lab-mcp -- autofde_lab.openclaw_http wrapping the
 * real autofde_lab.openclaw_bridge/_openclaw_runtime catalog()/execute()
 * dispatch). Distinct from lib/status.ts's fetchAutofdeLabStatus(),
 * which only reaches the namesake facts.json stub
 * (services/autofde-lab/app.py) -- zero calls into the actual
 * autofde_lab package. This module is the first caller that reaches the
 * real package's domain/solver registry.
 *
 * Same fail-closed convention as lib/status.ts: on any error (DNS,
 * refused connection, timeout, non-2xx, unparsable body, or a JSON-RPC
 * `error` member) this returns `{ ok: false, error }` -- never a
 * fabricated fallback catalog.
 */
export type OpenclawResult<T> = { ok: true; data: T } | { ok: false; error: string };

const FETCH_TIMEOUT_MS = 4000;

export interface OpenclawTool {
  name: string;
  description: string;
  inputSchema: unknown;
}

export interface OpenclawCatalogEntry {
  name: string;
  value?: string;
  group?: string;
  extras?: string[];
}

export interface OpenclawCatalog {
  domains?: OpenclawCatalogEntry[];
  solvers?: OpenclawCatalogEntry[];
}

function openclawMcpUrl(): string {
  return (
    process.env.AUTOFDE_LAB_MCP_URL ??
    "http://autofde-lab-mcp.autofde-lab.svc.cluster.local/rpc"
  );
}

let rpcId = 0;

async function callRpc<T>(method: string, params: Record<string, unknown>): Promise<OpenclawResult<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(openclawMcpUrl(), {
      method: "POST",
      signal: controller.signal,
      cache: "no-store",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: ++rpcId, method, params }),
    });
    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status} from ${openclawMcpUrl()}` };
    }
    const body = (await res.json()) as {
      result?: T;
      error?: { code: number; message: string };
    };
    if (body.error) {
      return { ok: false, error: `${body.error.code}: ${body.error.message}` };
    }
    if (body.result === undefined) {
      return { ok: false, error: "malformed JSON-RPC response: missing result" };
    }
    return { ok: true, data: body.result };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}

/** Real tools/list against the live bridge -- the MCP tool catalog (autofde_lab_catalog, _describe, _match, _run and their skdecide_* legacy aliases). */
export function fetchOpenclawToolCatalog() {
  return callRpc<{ tools: OpenclawTool[] }>("tools/list", {});
}

/**
 * Real tools/call of `autofde_lab_catalog` against the live bridge --
 * the actual registered domain/solver catalog
 * (autofde_lab.utils.get_registered_domains/get_registered_solvers via
 * importlib.metadata.entry_points), not the static facts.json snapshot.
 */
export async function fetchOpenclawDomainSolverCatalog(
  kind: "all" | "domains" | "solvers" = "all",
): Promise<OpenclawResult<OpenclawCatalog>> {
  const result = await callRpc<{ content: Array<{ type: string; text: string }> }>("tools/call", {
    name: "autofde_lab_catalog",
    arguments: { kind },
  });
  if (!result.ok) return result;
  const text = result.data.content?.[0]?.text;
  if (!text) return { ok: false, error: "malformed tools/call response: missing content[0].text" };
  let parsed: { ok?: boolean; result?: OpenclawCatalog; error?: unknown };
  try {
    parsed = JSON.parse(text);
  } catch (err) {
    return { ok: false, error: `unparsable tool result: ${err instanceof Error ? err.message : String(err)}` };
  }
  if (!parsed.ok || !parsed.result) {
    return { ok: false, error: `tool call failed: ${JSON.stringify(parsed.error ?? parsed)}` };
  }
  return { ok: true, data: parsed.result };
}
