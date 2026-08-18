/**
 * Server-side, read-only proxy to a project's real Supabase Storage API
 * (GET /bucket). Same convention as lib/gotrue.ts: Storage requires a
 * service-role key via the `apikey`/`Authorization` headers; without one
 * configured this reports "not configured" rather than a fabricated
 * bucket list.
 */

export type StorageAdminResult =
  | { ok: true; bucketCount: number; bucketNames: string[] }
  | { ok: false; notConfigured: true }
  | { ok: false; notConfigured: false; error: string };

const FETCH_TIMEOUT_MS = 3000;

export async function fetchStorageBuckets(
  dns: string,
  port: number,
): Promise<StorageAdminResult> {
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceRoleKey) {
    return { ok: false, notConfigured: true };
  }

  const url = `http://${dns}:${port}/bucket`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${serviceRoleKey}`,
        apikey: serviceRoleKey,
        accept: "application/json",
      },
    });
    if (!res.ok) {
      return { ok: false, notConfigured: false, error: `HTTP ${res.status} from ${url}` };
    }
    const body = (await res.json()) as Array<{ name: string }>;
    return {
      ok: true,
      bucketCount: body.length,
      bucketNames: body.map((b) => b.name),
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, notConfigured: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}
