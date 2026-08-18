"use client";

import { useState } from "react";

/**
 * POSTs { functionSlug, payload } to
 * /api/projects/[name]/functions/invoke -> lib/functions-api.ts's
 * invokeEdgeFunction, a real HTTP call to the project's real
 * edge-functions Service. Renders exactly the real status code and real
 * response body that pod sent back -- no client-side simulation of
 * "invoked".
 */
export default function InvokeFunctionButton({ projectName }: { projectName: string }) {
  const [open, setOpen] = useState(false);
  const [functionSlug, setFunctionSlug] = useState("health-check");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ status: number; body: string; durationMs: number } | null>(
    null,
  );

  async function onInvoke() {
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/functions/invoke`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ functionSlug, payload: {} }),
      });
      const responseBody = await res.json();
      if (!res.ok) {
        setError(responseBody.error ?? `HTTP ${res.status}`);
        return;
      }
      setResult({
        status: responseBody.status,
        body: responseBody.body,
        durationMs: responseBody.durationMs,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => {
          setOpen(true);
          setError(null);
          setResult(null);
        }}
        className="rounded-md border border-emerald-800 bg-emerald-950/30 px-3 py-1.5 text-xs font-medium text-emerald-300 hover:bg-emerald-950/60"
      >
        Invoke a function
      </button>
    );
  }

  return (
    <div className="mt-2 max-w-md space-y-2 rounded-md border border-border bg-black/20 p-3">
      <label className="block text-xs text-gray-400">
        Function slug (first path segment the runtime&apos;s router reads)
      </label>
      <input
        type="text"
        value={functionSlug}
        onChange={(e) => setFunctionSlug(e.target.value)}
        placeholder="health-check"
        className="w-full rounded-md border border-border bg-black/30 px-2 py-1 text-xs text-white"
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onInvoke}
          disabled={submitting || !functionSlug.trim()}
          className="rounded-md bg-emerald-700 px-3 py-1 text-xs font-medium text-white disabled:opacity-40"
        >
          {submitting ? "Invoking..." : "POST /" + (functionSlug || "<slug>")}
        </button>
        <button
          type="button"
          onClick={() => {
            setOpen(false);
            setError(null);
            setResult(null);
          }}
          disabled={submitting}
          className="rounded-md border border-border px-3 py-1 text-xs text-gray-300"
        >
          Cancel
        </button>
      </div>
      {error && (
        <p className="max-w-xl break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
      {result && (
        <div className="max-w-xl space-y-1 rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-200">
          <p>
  real response &mdash; HTTP <span className="font-semibold">{result.status}</span> in{" "}
            {result.durationMs}ms
          </p>
          <pre className="overflow-x-auto whitespace-pre-wrap break-all text-emerald-100">
            {result.body}
          </pre>
        </div>
      )}
    </div>
  );
}
