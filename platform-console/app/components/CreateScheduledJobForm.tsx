"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

interface AllowedCommandOption {
  id: string;
  label: string;
  description: string;
}

/**
 * POSTs a real k8s CronJob via /api/scheduled-jobs -> lib/scheduled-jobs.ts.
 * The command is always picked from the fixed, server-enforced allowlist
 * rendered as a <select> here -- there is no free-text command field in
 * this form, matching the API route's own "no raw command text accepted"
 * boundary. No client-side simulation of "created": the form shows
 * whatever the k8s API actually returned and only clears/refreshes on a
 * real 201.
 */
export default function CreateScheduledJobForm({
  namespaces,
  commands,
}: {
  namespaces: string[];
  commands: AllowedCommandOption[];
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [namespace, setNamespace] = useState(namespaces[0] ?? "");
  const [schedule, setSchedule] = useState("*/5 * * * *");
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
      const res = await fetch("/api/scheduled-jobs", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, namespace, schedule, commandId }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSuccess(
        `Created CronJob/${body.job.name} in namespace ${body.job.namespace} on schedule "${body.job.schedule}"`,
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
      <h2 className="text-base font-medium text-white">Create scheduled job</h2>
      <p className="text-xs text-gray-500">
        Submits a real <code>batch/v1</code> <code>CronJob</code> to the
        cluster via the console&apos;s ServiceAccount. The command a job
        runs is always one of a fixed, server-validated set below -- this
        form has no free-text command field, and the API route rejects
        anything outside that set before it ever reaches the cluster.
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
            placeholder="nightly-status-check"
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
          <span className="mb-1 block text-gray-400">Schedule (5-field cron)</span>
          <input
            required
            pattern="(\*|[0-9,\-/*]+)( (\*|[0-9,\-/*]+)){4}"
            title="5-field cron: minute hour day-of-month month day-of-week"
            value={schedule}
            onChange={(e) => setSchedule(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 font-mono text-sm text-white"
            placeholder="*/5 * * * *"
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
        {submitting ? "Creating..." : "Create scheduled job"}
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
