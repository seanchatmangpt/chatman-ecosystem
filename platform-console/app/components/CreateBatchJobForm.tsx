"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

interface AllowedBatchCommandOption {
  id: string;
  label: string;
  description: string;
}

/**
 * POSTs a real Indexed `batch/v1` Job via /api/batch-jobs ->
 * lib/batch-jobs.ts. Same "no free-text command field" boundary as
 * CreateScheduledJobForm: the command is always picked from the fixed,
 * server-enforced allowlist rendered as a <select> here. `size` sets both
 * `parallelism` and `completions` -- this form only ever launches a real,
 * pure fan-out job, never a queue-shaped one.
 */
export default function CreateBatchJobForm({
  namespaces,
  commands,
  minSize,
  maxSize,
}: {
  namespaces: string[];
  commands: AllowedBatchCommandOption[];
  minSize: number;
  maxSize: number;
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [namespace, setNamespace] = useState(namespaces[0] ?? "");
  const [size, setSize] = useState(Math.min(5, maxSize));
  const [commandId, setCommandId] = useState(commands[0]?.id ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch("/api/batch-jobs", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, namespace, size, commandId }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSuccess(
        `Launched Job/${body.job.name} in namespace ${body.job.namespace}: parallelism=${body.job.parallelism}, completions=${body.job.completions}`,
      );
      setName("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card space-y-4 p-6">
      <h2 className="text-base font-medium text-white">Launch a batch job</h2>
      <p className="text-xs text-gray-500">
        Submits a real Indexed <code>batch/v1</code> <code>Job</code> (
        <code>completionMode: Indexed</code>) to the cluster via the console&apos;s
        ServiceAccount -- <code>size</code> below sets both <code>parallelism</code> and{" "}
        <code>completions</code>, so every pod launches at once, each with its own real{" "}
        <code>JOB_COMPLETION_INDEX</code>. The command a pod runs is always one of a fixed,
        server-validated set below -- no free-text command field.
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Name</span>
          <input
            required
            pattern="[a-z0-9]([-a-z0-9]*[a-z0-9])?"
            title="lowercase alphanumeric and '-', RFC 1123 label"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            placeholder="fanout-demo"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Namespace</span>
          <select
            required
            value={namespace}
            onChange={(e) => setNamespace(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          >
            {namespaces.map((ns) => (
              <option key={ns} value={ns}>
                {ns}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">
            Size (parallelism = completions, {minSize}-{maxSize})
          </span>
          <input
            required
            type="number"
            min={minSize}
            max={maxSize}
            value={size}
            onChange={(e) => setSize(Number(e.target.value))}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Command (allowlisted)</span>
          <select
            required
            value={commandId}
            onChange={(e) => setCommandId(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          >
            {commands.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p className="text-xs text-gray-500">
        {commands.find((c) => c.id === commandId)?.description}
      </p>

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Launching..." : "Launch batch job"}
      </button>
      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
      {success && (
        <p className="break-all rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-300">
          {success}
        </p>
      )}
    </form>
  );
}
