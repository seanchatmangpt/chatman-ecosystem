"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * DELETEs a real k8s Secret via /api/secrets -> lib/k8s.ts. No client-side
 * simulation of "deleted" -- the row only disappears (via router.refresh())
 * after a real 200 from the API route.
 */
export default function DeleteSecretButton({
  namespace,
  name,
}: {
  namespace: string;
  name: string;
}) {
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onDelete() {
    if (!confirm(`Delete Secret/${name} in namespace ${namespace}? This cannot be undone.`)) {
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      const res = await fetch(
        `/api/secrets?namespace=${encodeURIComponent(namespace)}&name=${encodeURIComponent(name)}`,
        { method: "DELETE" },
      );
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={onDelete}
        disabled={deleting}
        className="rounded-md border border-red-900 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
      >
        {deleting ? "Deleting..." : "Delete"}
      </button>
      {error && <p className="max-w-xs break-all text-right text-xs text-red-400">{error}</p>}
    </div>
  );
}
