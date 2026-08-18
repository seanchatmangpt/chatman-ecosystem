"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * POSTs to /api/projects/[name]/backups -> lib/k8s.ts's createBackupJob,
 * which creates a real batch/v1 Job that runs pg_dump against this
 * project's real Postgres Pod (resolved live server-side via
 * getProjectDatabasePod -- never a literal `demo-db-postgres`). No
 * client-side simulation of "backed up" -- the new row only appears (via
 * router.refresh()) after a real 201 with the real Job the API server
 * accepted; the Job's own status (Pending/Running/Complete/Failed) is
 * whatever listJobs next observes from the cluster, not set here.
 */
export default function RunBackupButton({ projectName }: { projectName: string }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onRun() {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/backups`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSuccess(`Created Job/${body.job.name} -- refresh to watch it reach Complete`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={onRun}
        disabled={submitting}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Starting backup..." : "Run backup now"}
      </button>
      {error && (
        <p className="max-w-xl break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
      {success && (
        <p className="max-w-xl break-all rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-300">
          {success}
        </p>
      )}
    </div>
  );
}
