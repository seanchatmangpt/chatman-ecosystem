"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * POSTs {version, name, upSql, downSql} to
 * /api/projects/[name]/migrations -> lib/migrations.ts's applyMigration,
 * which runs upSql in a real transaction against this project's live
 * Postgres and records the row in platform_console.schema_migrations only
 * on success. No client-side simulation of "applied" -- the new history
 * row only appears (via router.refresh()) after a real 201 the API server
 * returned.
 */
export default function ApplyMigrationForm({ projectName }: { projectName: string }) {
  const router = useRouter();
  const [version, setVersion] = useState("");
  const [name, setName] = useState("");
  const [upSql, setUpSql] = useState("");
  const [downSql, setDownSql] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/migrations`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          action: "apply",
          version: Number(version),
          name,
          upSql,
          downSql,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSuccess(`Applied migration v${body.migration.version} (${body.migration.name})`);
      setVersion("");
      setName("");
      setUpSql("");
      setDownSql("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Version</span>
          <input
            type="number"
            min={1}
            step={1}
            required
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            placeholder="1"
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block text-sm sm:col-span-2">
          <span className="mb-1 block text-gray-400">Name</span>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="add_widget_orders_table"
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
      </div>
      <label className="block text-sm">
        <span className="mb-1 block text-gray-400">Up SQL</span>
        <textarea
          required
          value={upSql}
          onChange={(e) => setUpSql(e.target.value)}
          rows={6}
          placeholder="CREATE TABLE ..."
          className="w-full rounded-md border border-border bg-bg px-3 py-2 font-mono text-xs text-white"
        />
      </label>
      <label className="block text-sm">
        <span className="mb-1 block text-gray-400">Down SQL</span>
        <textarea
          required
          value={downSql}
          onChange={(e) => setDownSql(e.target.value)}
          rows={6}
          placeholder="DROP TABLE ..."
          className="w-full rounded-md border border-border bg-bg px-3 py-2 font-mono text-xs text-white"
        />
      </label>
      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Applying..." : "Apply migration"}
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
    </form>
  );
}
