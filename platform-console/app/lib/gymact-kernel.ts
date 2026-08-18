/**
 * Server-side client for the real gymact FastAPI kernel
 * (src/gymact/surfaces/fastapi.py's create_app -- the actual
 * materialize/act/verify/checkpoint DCM surface), NOT the static
 * gymact-status facts.json exporter lib/status.ts already talks to.
 * Same fail-closed convention as lib/status.ts: any transport error,
 * timeout, or non-2xx status returns an honest `{ ok: false }` --
 * this module never fabricates a fallback episode/receipt.
 *
 * The kernel Service (gymact-kernel.gymact.svc.cluster.local:8000) runs
 * the real ProductionGymAct with a MemoryProvider registered
 * (gymact.surfaces.fastapi._runtime's default), matching what
 * `gymact serve` runs in production. It is a distinct k8s Deployment/
 * Service from gymact-status (see k8s/services-and-deployments.yaml's
 * "gymact-kernel" block) -- gymact-status only re-serves a build-time
 * facts.json snapshot and has no /episodes surface at all.
 */

export type KernelResult<T> = { ok: true; data: T } | { ok: false; error: string };

const FETCH_TIMEOUT_MS = 5000;

function kernelBaseUrl(): string {
  return process.env.GYMACT_KERNEL_URL ?? "http://gymact-kernel.gymact.svc.cluster.local:8000";
}

async function kernelFetch<T>(path: string, init?: RequestInit): Promise<KernelResult<T>> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(`${kernelBaseUrl()}${path}`, {
      ...init,
      signal: controller.signal,
      cache: "no-store",
      headers: { accept: "application/json", "content-type": "application/json", ...init?.headers },
    });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      return { ok: false, error: `HTTP ${res.status} from ${path}: ${body.slice(0, 300)}` };
    }
    return { ok: true, data: (await res.json()) as T };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, error: `unreachable: ${message}` };
  } finally {
    clearTimeout(timeout);
  }
}

export interface KernelHealth {
  status: string;
  version: string;
  contract_digest: string;
}

export interface KernelProviders {
  providers: string[];
}

export interface KernelEvidenceRecord {
  sequence: number;
  previous_digest: string | null;
  receipt_digest: string;
  record_digest: string;
  receipt: Record<string, unknown>;
}

export interface KernelEvidence {
  verified: boolean;
  records: KernelEvidenceRecord[];
}

export interface KernelEpisode {
  episode_id: string;
  provider: string;
  environment_id: string;
  scenario: string | null;
  standing: string;
}

export interface KernelMaterializeResult {
  accepted: boolean;
  standing: string;
  episode: KernelEpisode;
  observation: { episode_id: string; state: Record<string, unknown>; state_digest: string };
  receipt: Record<string, unknown>;
}

export interface KernelVerifyResult {
  verification_id: string;
  episode_id: string;
  passed: boolean;
  expected: Record<string, unknown>;
  observed: Record<string, unknown>;
  state_digest: string;
}

export function fetchKernelHealth() {
  return kernelFetch<KernelHealth>("/health");
}

export function fetchKernelProviders() {
  return kernelFetch<KernelProviders>("/providers");
}

export function fetchKernelEvidence() {
  return kernelFetch<KernelEvidence>("/evidence");
}

/**
 * Real, minimal DO-path exercise: materialize one bounded `memory`
 * provider episode, then independently verify it (`expected: {}` against
 * the freshly-materialized empty state, always true for the memory
 * provider's initial state). This is a live probe of the actual DCM
 * production DO path -- the same operation an autonomous agent would
 * invoke -- not a synthetic canned reply; a real BoundaryBlocked/refusal
 * from the kernel surfaces here exactly as the kernel returned it.
 */
export async function probeKernelEpisode(): Promise<
  KernelResult<{ materialize: KernelMaterializeResult; verify: KernelVerifyResult }>
> {
  const materialize = await kernelFetch<KernelMaterializeResult>("/episodes", {
    method: "POST",
    body: JSON.stringify({ provider: "memory" }),
  });
  if (!materialize.ok) return materialize;

  const episodeId = materialize.data.episode.episode_id;
  const verify = await kernelFetch<KernelVerifyResult>(
    `/episodes/${episodeId}/verify`,
    { method: "POST", body: JSON.stringify({ expected: {} }) },
  );
  if (!verify.ok) return verify;

  return { ok: true, data: { materialize: materialize.data, verify: verify.data } };
}
