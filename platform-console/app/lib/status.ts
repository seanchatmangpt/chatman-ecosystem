/**
 * Server-side fetchers for each project's cluster-internal /status endpoint.
 * Each fetch is short-timeout and fails closed: on any error (DNS, refused
 * connection, timeout, non-2xx, unparsable body) the page renders
 * "unreachable" -- this module never fabricates a fallback status object.
 */

export type StatusResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

const FETCH_TIMEOUT_MS = 3000;

async function fetchJson<T>(url: string): Promise<StatusResult<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json" },
    });
    if (!res.ok) {
      return { ok: false, error: `HTTP ${res.status} from ${url}` };
    }
    const data = (await res.json()) as T;
    return { ok: true, data };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}

export interface AutofdeLabStatus {
  service: string;
  repo: string;
  git_head: string;
  git_head_subject: string;
  justfile_targets_present: string[];
  checked_at: string;
}

export interface GymactStatus {
  service: string;
  repo: string;
  git_head: string;
  cli_version: string;
  providers: { builtins: string[] };
  checked_at: string;
}

export interface GgenStatus {
  service: string;
  repo: string;
  git_head: string;
  installed_binary_version: string;
  workspace_cargo_version: string;
  sync_run_subcommand_present: boolean;
  checked_at: string;
}

export interface GgenMarketplaceStatus {
  service: string;
  repo: string;
  git_head: string;
  pack_count: number;
  checked_at: string;
}

export { fetchOpenclawDomainSolverCatalog, fetchOpenclawToolCatalog } from "@/lib/openclaw";

export function fetchAutofdeLabStatus() {
  const url =
    process.env.AUTOFDE_LAB_STATUS_URL ??
    "http://autofde-lab-status.autofde-lab.svc.cluster.local/status";
  return fetchJson<AutofdeLabStatus>(url);
}

export function fetchGymactStatus() {
  const url =
    process.env.GYMACT_STATUS_URL ??
    "http://gymact-status.gymact.svc.cluster.local/status";
  return fetchJson<GymactStatus>(url);
}

export function fetchGgenStatus() {
  const url =
    process.env.GGEN_STATUS_URL ??
    "http://ggen-status.ggen.svc.cluster.local/status";
  return fetchJson<GgenStatus>(url);
}

export function fetchGgenMarketplaceStatus() {
  const url =
    process.env.GGEN_MARKETPLACE_STATUS_URL ??
    "http://ggen-marketplace-status.ggen-marketplace.svc.cluster.local/status";
  return fetchJson<GgenMarketplaceStatus>(url);
}
