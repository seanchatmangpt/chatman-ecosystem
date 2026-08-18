"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * POSTs { action: "restore", backupJobName, confirm } to /api/backups ->
 * lib/k8s.ts's createRestoreJob, which creates a real batch/v1 Job that
 * drops the target database's schemas and replays this backup's real
 * pg_dump SQL into it. This is destructive-ish (it overwrites the target
 * database's current contents with whatever this backup captured), so the
 * confirmation step requires typing the exact backup Job name -- checked
 * again server-side in the route handler, never trusted from a disabled
 * button alone. No client-side simulation of "restored" -- the new row in
 * the restore table only appears (via router.refresh()) after a real 201
 * with the real Job the API server accepted.
 */
export default function RestoreBackupButton({ backupJobName }: { backupJobName: string }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onRestore() {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch("/api/backups", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ action: "restore", backupJobName, confirm: confirmText }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSuccess(`Created Job/${body.job.name} -- refresh to watch it reach Complete`);
      setOpen(false);
      setConfirmText("");
      router.refresh();
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
          setSuccess(null);
        }}
        className="rounded-md border border-amber-800 bg-amber-950/30 px-2 py-1 text-xs font-medium text-amber-300 hover:bg-amber-950/60"
      >
        Restore
      </button>
    );
  }

  return (
    <div className="mt-2 max-w-md space-y-2 rounded-md border border-amber-900 bg-amber-950/20 p-3">
      <p className="text-xs text-amber-200">
        This overwrites the current contents of <code>demo-db-postgres-0</code> with
        this backup&apos;s data. Type the backup name to confirm:{" "}
        <code className="break-all text-white">{backupJobName}</code>
      </p>
      <input
        type="text"
        value={confirmText}
        onChange={(e) => setConfirmText(e.target.value)}
        placeholder={backupJobName}
        className="w-full rounded-md border border-border bg-black/30 px-2 py-1 text-xs text-white"
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onRestore}
          disabled={submitting || confirmText !== backupJobName}
          className="rounded-md bg-red-700 px-3 py-1 text-xs font-medium text-white disabled:opacity-40"
        >
          {submitting ? "Starting restore..." : "Confirm restore"}
        </button>
        <button
          type="button"
          onClick={() => {
            setOpen(false);
            setConfirmText("");
            setError(null);
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
      {success && (
        <p className="max-w-xl break-all rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-300">
          {success}
        </p>
      )}
    </div>
  );
}
