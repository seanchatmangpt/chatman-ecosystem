"use client";

import { useEffect, useState } from "react";
import type { OcelAccumulatorStatus, OcelDiscoveryResult } from "@/lib/ocel-log";

type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

interface OcelLogApiResponse {
  status: ApiResult<OcelAccumulatorStatus>;
  discovery: ApiResult<OcelDiscoveryResult>;
}

const POLL_INTERVAL_MS = 10_000;

// Client-side polling panel for /api/ocel-log, mirroring /tracing's
// server-rendered fail-closed convention but polling in-browser so the
// growing event count is visible without a manual reload -- the plan's
// explicit ask for step D. Every fetch hits the real proxy route; a
// { ok: false } from the accumulator (including "not deployed yet") is
// rendered verbatim, never hidden or retried into a fabricated number.
export default function OcelLogPanel() {
  const [data, setData] = useState<OcelLogApiResponse | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const res = await fetch("/api/ocel-log", { cache: "no-store" });
        if (!res.ok) {
          if (!cancelled) setFetchError(`HTTP ${res.status} from /api/ocel-log`);
          return;
        }
        const body = (await res.json()) as OcelLogApiResponse;
        if (!cancelled) {
          setData(body);
          setFetchError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setFetchError(err instanceof Error ? err.message : String(err));
        }
      }
    }

    poll();
    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (fetchError) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
        {fetchError}
      </p>
    );
  }

  if (!data) {
    return <p className="text-sm text-gray-500">loading...</p>;
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">accumulator status</h2>
        {!data.status.ok && (
          <div className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
            {data.status.error}
          </div>
        )}
        {data.status.ok && (
          <dl className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <dt className="text-gray-500">event count</dt>
              <dd className="text-lg text-white">{data.status.data.eventCount}</dd>
            </div>
            <div>
              <dt className="text-gray-500">object count</dt>
              <dd className="text-lg text-white">{data.status.data.objectCount}</dd>
            </div>
            <div>
              <dt className="text-gray-500">last updated</dt>
              <dd className="text-white">
                {new Date(data.status.data.lastUpdated).toLocaleString()}
              </dd>
            </div>
          </dl>
        )}
      </div>

      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">
          discovery result (<code>wasm4pm-cli</code>)
        </h2>
        {!data.discovery.ok && (
          <div className="rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
            {data.discovery.error}
          </div>
        )}
        {data.discovery.ok && (
          <pre className="overflow-x-auto rounded-md bg-black/40 p-4 text-xs text-gray-200">
            {JSON.stringify(data.discovery.data, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
