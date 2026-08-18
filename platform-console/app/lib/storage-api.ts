/**
 * Server-side, read-only proxy to a project's real Supabase Storage API
 * (GET /bucket for listing, GET /object/{bucket}/{path} for one object's
 * bytes -- see fetchStorageObject below). Same convention as
 * lib/gotrue.ts: Storage requires a service-role key via the
 * `apikey`/`Authorization` headers; without one configured this reports
 * "not configured" rather than a fabricated bucket list or object body.
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

export type StorageObjectResult =
  | { ok: true; body: ArrayBuffer; contentType: string }
  | { ok: false; notConfigured: true }
  | { ok: false; notConfigured: false; status: number; error: string };

/**
 * Server-side, read-only proxy to one real object's bytes (GET
 * /object/{bucket}/{objectPath}) on the same real Supabase Storage API
 * fetchStorageBuckets already talks to -- the download half of the
 * signed-URL flow (lib/storage-signed-url.ts mints/verifies the token;
 * this function is only ever called AFTER that verification succeeds, by
 * app/api/projects/[name]/storage/download/route.ts). Same
 * SUPABASE_SERVICE_ROLE_KEY "not configured" fail-closed convention as
 * fetchStorageBuckets -- a signed, unexpired token is still not enough to
 * fetch real bytes from an unconfigured Storage API.
 */
export async function fetchStorageObject(
  dns: string,
  port: number,
  bucket: string,
  objectPath: string,
): Promise<StorageObjectResult> {
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceRoleKey) {
    return { ok: false, notConfigured: true };
  }

  const url = `http://${dns}:${port}/object/${encodeURIComponent(bucket)}/${objectPath
    .split("/")
    .map(encodeURIComponent)
    .join("/")}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${serviceRoleKey}`,
        apikey: serviceRoleKey,
      },
    });
    if (!res.ok) {
      return {
        ok: false,
        notConfigured: false,
        status: res.status,
        error: `HTTP ${res.status} from ${url}`,
      };
    }
    const body = await res.arrayBuffer();
    return {
      ok: true,
      body,
      contentType: res.headers.get("content-type") ?? "application/octet-stream",
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, notConfigured: false, status: 502, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}
