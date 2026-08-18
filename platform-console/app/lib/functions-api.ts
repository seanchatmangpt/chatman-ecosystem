/**
 * Server-side proxy to a project's real Supabase Edge Functions runtime
 * (supabase/edge-runtime, started with `--main-service`). Same convention
 * as lib/gotrue.ts / lib/storage-api.ts: the runtime requires a real JWT
 * (VERIFY_JWT=true in every project's functions Deployment) via the
 * `Authorization` header, so without SUPABASE_SERVICE_ROLE_KEY configured
 * this reports "not configured" rather than a fabricated invocation.
 *
 * The runtime's own router (the project's "main" Function -- see
 * demo-project-main-function ConfigMap) reads the first path segment as
 * the function slug and does
 * `EdgeRuntime.userWorkers.create({ servicePath: /home/deno/functions/<slug>, ... })`.
 * That means POST /<slug> against port 9000 is the *real* invoke surface --
 * there is no separate "/functions/v1/<slug>" prefix on this in-cluster
 * Service (Envoy/Kong adds that prefix at the project's public gateway;
 * this module talks to the functions Service directly, same as every
 * other lib/*-api.ts module talks to its Service directly).
 */

export type FunctionInvokeResult =
  | { ok: true; status: number; body: string; durationMs: number }
  | { ok: false; notConfigured: true }
  | { ok: false; notConfigured: false; error: string };

const FETCH_TIMEOUT_MS = 10_000;

/** dns is the functions Service's cluster DNS name, e.g. demo-project-functions.supabase-demo.svc.cluster.local */
export async function invokeEdgeFunction(
  dns: string,
  port: number,
  functionSlug: string,
  payload: unknown,
): Promise<FunctionInvokeResult> {
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceRoleKey) {
    return { ok: false, notConfigured: true };
  }

  const url = `http://${dns}:${port}/${encodeURIComponent(functionSlug)}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  const startedAt = Date.now();
  try {
    const res = await fetch(url, {
      method: "POST",
      signal: controller.signal,
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${serviceRoleKey}`,
        apikey: serviceRoleKey,
        "content-type": "application/json",
      },
      body: JSON.stringify(payload ?? {}),
    });
    const durationMs = Date.now() - startedAt;
    const body = await res.text();
    return { ok: true, status: res.status, body, durationMs };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, notConfigured: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}
