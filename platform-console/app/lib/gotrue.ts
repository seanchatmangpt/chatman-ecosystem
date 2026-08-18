/**
 * Server-side, read-only proxy to a project's real GoTrue (Supabase Auth)
 * admin API. GoTrue's /admin/users endpoint requires a service-role JWT --
 * this console has no such key provisioned for any project by default, so
 * the honest behavior (never fabricate a user count) is to report
 * "not configured" rather than guess. If SUPABASE_SERVICE_ROLE_KEY is set
 * in the console's environment, the real call is made and the real count
 * returned.
 */

export type GoTrueAdminResult =
  | { ok: true; userCount: number }
  | { ok: false; notConfigured: true }
  | { ok: false; notConfigured: false; error: string };

const FETCH_TIMEOUT_MS = 3000;

/** dns is the auth Service's cluster DNS name, e.g. demo-project-auth.supabase-demo.svc.cluster.local */
export async function fetchGoTrueUserCount(
  dns: string,
  port: number,
): Promise<GoTrueAdminResult> {
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceRoleKey) {
    return { ok: false, notConfigured: true };
  }

  const url = `http://${dns}:${port}/admin/users?per_page=1`;
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
      return {
        ok: false,
        notConfigured: false,
        error: `HTTP ${res.status} from ${url}`,
      };
    }
    const body = (await res.json()) as { users?: unknown[]; total?: number };
    const userCount =
      typeof body.total === "number" ? body.total : (body.users?.length ?? 0);
    return { ok: true, userCount };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, notConfigured: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}
