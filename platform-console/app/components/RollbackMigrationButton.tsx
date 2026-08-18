"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * POSTs { action: "rollback", version, confirm } to
 * /api/projects/[name]/migrations -> lib/migrations.ts's
 * rollbackMigration, which replays the migration's own stored downSql in a
 * real transaction and deletes its row on success. Destructive (it undoes
 * a real, already-applied schema change), so the confirmation step
 * requires typing the exact version number -- checked again server-side,
 * never trusted from a disabled button alone (same convention as
 * RestoreBackupButton).
 */
export default function RollbackMigrationButton({
  projectName,
  version,
  name,
}: {
  projectName: string;
  version: number;
  name: string;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [confirmText, setConfirmText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onRollback() {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/migrations`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ action: "rollback", version, confirm: confirmText }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
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
        }}
        className="rounded-md border border-amber-800 bg-amber-950/30 px-2 py-1 text-xs font-medium text-amber-300 hover:bg-amber-950/60"
      >
        Rollback
      </button>
    );
  }

  return (
    <div className="mt-2 max-w-md space-y-2 rounded-md border border-amber-900 bg-amber-950/20 p-3">
      <p className="text-xs text-amber-200">
        This runs migration v{version} (&quot;{name}&quot;)&apos;s stored down SQL and removes
        its history row. Type <code className="text-white">{version}</code> to confirm:
      </p>
      <input
        type="text"
        value={confirmText}
        onChange={(e) => setConfirmText(e.target.value)}
        placeholder={String(version)}
        className="w-full rounded-md border border-border bg-black/30 px-2 py-1 text-xs text-white"
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onRollback}
          disabled={submitting || confirmText !== String(version)}
          className="rounded-md bg-red-700 px-3 py-1 text-xs font-medium text-white disabled:opacity-40"
        >
          {submitting ? "Rolling back..." : "Confirm rollback"}
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
    </div>
  );
}
