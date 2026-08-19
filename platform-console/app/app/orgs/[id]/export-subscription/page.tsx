"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Nav from "@/components/Nav";

interface SubscriptionState {
  orgId: string;
  bucketEndpoint: string;
  bucketName: string;
  prefix: string;
  cadence: "daily" | "weekly";
  scope: "audit-log" | "full-export";
  enabled: boolean;
  lastRunAt: string | null;
  lastRunStatus: "success" | "error" | null;
  updatedAt: string;
  updatedBy: string;
  hasCredentials: boolean;
}

interface RunRow {
  runId: string;
  ranAt: string;
  status: "success" | "error";
  objectKey: string | null;
  bytesWritten: number | null;
  error: string | null;
}

interface LoadedState {
  subscription: SubscriptionState | null;
  runs: RunRow[];
  cronSchedule: string | null;
  encryptionConfigured: boolean;
}

// Real "bring your own bucket" scheduled export subscription page,
// backing lib/s3-export-subscription.ts and
// app/api/orgs/[id]/export-subscription/route.ts. Owner-only writes,
// maker-checker gated server-side (`export-subscription.update`) -- this
// page submits the form, but the API route may hand back
// `status: "pending_approval"` instead of saving, exactly the same
// "202, not 200" shape app/org/region/page.tsx's own PUT already models
// for its own gated write, one step up (a SECOND owner must also POST
// /api/approvals/[id] before a retry of this same form actually saves).
export default function ExportSubscriptionPage() {
  const params = useParams<{ id: string }>();
  const orgId = params?.id ?? "";

  const [state, setState] = useState<LoadedState | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [bucketEndpoint, setBucketEndpoint] = useState("");
  const [bucketName, setBucketName] = useState("");
  const [accessKeyId, setAccessKeyId] = useState("");
  const [secretAccessKey, setSecretAccessKey] = useState("");
  const [prefix, setPrefix] = useState("");
  const [cadence, setCadence] = useState<"daily" | "weekly">("daily");
  const [scope, setScope] = useState<"audit-log" | "full-export">("audit-log");
  const [enabled, setEnabled] = useState(true);

  function load() {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(orgId)}/export-subscription`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        setState(body as LoadedState);
        if (body.subscription) {
          const s = body.subscription as SubscriptionState;
          setBucketEndpoint(s.bucketEndpoint);
          setBucketName(s.bucketName);
          setPrefix(s.prefix);
          setCadence(s.cadence);
          setScope(s.scope);
          setEnabled(s.enabled);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, [orgId]);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId) return;
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/export-subscription`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          bucketEndpoint,
          bucketName,
          accessKeyId,
          secretAccessKey,
          prefix,
          cadence,
          scope,
          enabled,
        }),
      });
      const body = await res.json();
      if (res.status === 202) {
        setNotice(body.message ?? "pending a second owner's approval");
        return;
      }
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setNotice("Export subscription saved.");
      setAccessKeyId("");
      setSecretAccessKey("");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleRunNow() {
    if (!orgId) return;
    setRunning(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/export-subscription`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ action: "run" }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setNotice(
        body.run.status === "success"
          ? `Run succeeded -- wrote ${body.run.bytesWritten} bytes to ${body.run.objectKey}`
          : `Run failed: ${body.run.error}`,
      );
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Scheduled export to your bucket</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Deliver this org&apos;s audit log or full export bundle to an S3-compatible bucket you own
          (AWS S3, MinIO, or any other S3-compatible endpoint) on a daily or weekly schedule -- for
          SIEM/data-lake ingestion. Bucket credentials are encrypted at rest and never returned by
          this page after saving. Saving a new or changed subscription requires a second, distinct
          owner-role approver (<code>POST /api/approvals/[id]</code>) before it takes effect.
        </p>

        {state && !state.encryptionConfigured && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            not configured: this deployment has no{" "}
            <code>EXPORT_SUBSCRIPTION_ENCRYPTION_KEY</code> set. Saving will fail until a 32-byte
            hex key is provisioned -- credentials are never stored unencrypted.
          </div>
        )}

        {loading && <p className="text-sm text-gray-400">loading...</p>}

        <form onSubmit={handleSave} className="mb-10 space-y-5">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Bucket endpoint</label>
              <input
                value={bucketEndpoint}
                onChange={(e) => setBucketEndpoint(e.target.value)}
                placeholder="https://s3.us-east-1.amazonaws.com or https://minio.example.com"
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Bucket name</label>
              <input
                value={bucketName}
                onChange={(e) => setBucketName(e.target.value)}
                placeholder="acme-siem-ingest"
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Access key ID</label>
              <input
                value={accessKeyId}
                onChange={(e) => setAccessKeyId(e.target.value)}
                placeholder={
                  state?.subscription?.hasCredentials ? "unchanged -- leave blank to keep current key" : ""
                }
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Secret access key</label>
              <input
                type="password"
                value={secretAccessKey}
                onChange={(e) => setSecretAccessKey(e.target.value)}
                placeholder={
                  state?.subscription?.hasCredentials ? "unchanged -- leave blank to keep current key" : ""
                }
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Object key prefix</label>
              <input
                value={prefix}
                onChange={(e) => setPrefix(e.target.value)}
                placeholder="platform-console/"
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Cadence</label>
              <select
                value={cadence}
                onChange={(e) => setCadence(e.target.value as "daily" | "weekly")}
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Scope</label>
              <select
                value={scope}
                onChange={(e) => setScope(e.target.value as "audit-log" | "full-export")}
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              >
                <option value="audit-log">Audit log (NDJSON)</option>
                <option value="full-export">Full export bundle (zip)</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                id="enabled"
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="h-4 w-4 rounded border-gray-700 bg-gray-900"
              />
              <label htmlFor="enabled" className="text-sm text-gray-300">
                Enabled
              </label>
            </div>
          </div>

          {error && (
            <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
              {error}
            </p>
          )}
          {notice && !error && (
            <p className="rounded-md border border-emerald-900 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-300">
              {notice}
            </p>
          )}

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={saving || !orgId}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save subscription"}
            </button>
            <button
              type="button"
              onClick={handleRunNow}
              disabled={running || !state?.subscription}
              className="rounded-md border border-gray-700 px-4 py-2 text-sm font-medium text-gray-200 hover:bg-gray-800 disabled:opacity-50"
            >
              {running ? "Running..." : "Run now"}
            </button>
          </div>
        </form>

        {state?.subscription && (
          <div className="mb-8 rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-300">
            <p>
              Last run:{" "}
              {state.subscription.lastRunAt ? (
                <>
                  {new Date(state.subscription.lastRunAt).toLocaleString()} --{" "}
                  <span
                    className={
                      state.subscription.lastRunStatus === "success" ? "text-emerald-400" : "text-red-400"
                    }
                  >
                    {state.subscription.lastRunStatus}
                  </span>
                </>
              ) : (
                "never"
              )}
            </p>
            <p className="mt-1 text-gray-500">
              Cron schedule: <code>{state.cronSchedule}</code>
            </p>
          </div>
        )}

        <h2 className="mb-3 text-lg font-semibold text-white">Run history</h2>
        {(!state || state.runs.length === 0) && (
          <p className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-400">
            No runs yet.
          </p>
        )}
        {state && state.runs.length > 0 && (
          <div className="overflow-x-auto rounded-md border border-gray-800">
            <table className="min-w-full divide-y divide-gray-800 text-sm">
              <thead className="bg-gray-900/60 text-left text-gray-400">
                <tr>
                  <th className="px-4 py-2 font-medium">Ran at</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                  <th className="px-4 py-2 font-medium">Object key</th>
                  <th className="px-4 py-2 font-medium">Bytes</th>
                  <th className="px-4 py-2 font-medium">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {state.runs.map((r) => (
                  <tr key={r.runId} className="text-gray-200">
                    <td className="px-4 py-2 text-gray-400">{new Date(r.ranAt).toLocaleString()}</td>
                    <td className="px-4 py-2">
                      {r.status === "success" ? (
                        <span className="rounded-full bg-emerald-950/60 px-2 py-0.5 text-xs text-emerald-300">
                          success
                        </span>
                      ) : (
                        <span className="rounded-full bg-red-950/60 px-2 py-0.5 text-xs text-red-300">
                          error
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 font-mono text-xs">{r.objectKey ?? "--"}</td>
                    <td className="px-4 py-2 text-gray-400">{r.bytesWritten ?? "--"}</td>
                    <td className="px-4 py-2 text-red-400">{r.error ?? "--"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </>
  );
}
