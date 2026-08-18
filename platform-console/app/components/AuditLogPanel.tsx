"use client";

import { useState } from "react";
import type { AuditLogRow } from "@/lib/audit-db";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

/**
 * Real filter/pagination client for GET /api/audit -> lib/audit-db.ts's
 * queryAuditLog against the live platform_console.audit_log table. No
 * client-side fabrication of rows -- every render reflects the last real
 * 200 from the API route, same "no optimistic UI" convention every other
 * data panel in this console (OrgRolesPanel, FeatureFlagsPanel) follows.
 */
export default function AuditLogPanel({
  initialEntries,
  initialTotal,
  initialLimit,
}: {
  initialEntries: AuditLogRow[];
  initialTotal: number;
  initialLimit: number;
}) {
  const [entries, setEntries] = useState(initialEntries);
  const [total, setTotal] = useState(initialTotal);
  const [limit] = useState(initialLimit);
  const [page, setPage] = useState(1);
  const [actor, setActor] = useState("");
  const [path, setPath] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runQuery(nextPage: number) {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (actor.trim()) params.set("actor", actor.trim());
      if (path.trim()) params.set("path", path.trim());
      if (from) params.set("from", new Date(from).toISOString());
      if (to) params.set("to", new Date(to).toISOString());
      params.set("limit", String(limit));
      params.set("page", String(nextPage));

      const res = await fetch(`/api/audit?${params.toString()}`);
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setEntries(body.entries as AuditLogRow[]);
      setTotal(body.total as number);
      setPage(nextPage);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  function onFilterSubmit(e: React.FormEvent) {
    e.preventDefault();
    void runQuery(1);
  }

  function onExport() {
    // Real SIEM-format bulk export (GET /api/audit/export ->
    // lib/audit-export.ts's streamAuditLogAsEcsNdjson): reuses this same
    // panel's current from/to date-range filter (actor/path are display
    // filters only -- the export intentionally ships the full ECS-shaped
    // history for the date range, not a client-side-narrowed subset).
    // Plain navigation, not fetch+blob: the browser streams the response
    // straight to disk itself, honoring the route's own
    // Content-Disposition: attachment header, without this tab ever
    // buffering the export in JS memory.
    const params = new URLSearchParams();
    if (from) params.set("from", new Date(from).toISOString());
    if (to) params.set("to", new Date(to).toISOString());
    window.location.href = `/api/audit/export?${params.toString()}`;
  }

  function onReset() {
    setActor("");
    setPath("");
    setFrom("");
    setTo("");
    setEntries(initialEntries);
    setTotal(initialTotal);
    setPage(1);
    setError(null);
  }

  const totalPages = Math.max(1, Math.ceil(total / limit));

  return (
    <div className="space-y-6">
      <form onSubmit={onFilterSubmit} className="card grid gap-4 p-6 sm:grid-cols-4">
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Actor</span>
          <input
            value={actor}
            onChange={(e) => setActor(e.target.value)}
            placeholder="admin, user@example.com..."
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Path</span>
          <input
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="/api/projects..."
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">From</span>
          <input
            type="datetime-local"
            value={from}
            onChange={(e) => setFrom(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">To</span>
          <input
            type="datetime-local"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
        <div className="flex gap-2 sm:col-span-4">
          <button
            type="submit"
            disabled={loading}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
          <button
            type="button"
            onClick={onReset}
            disabled={loading}
            className="rounded-md border border-border px-4 py-2 text-sm text-gray-300 disabled:opacity-50"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={onExport}
            disabled={loading}
            title="Streams the full ECS-shaped NDJSON export for the From/To range above (owner-only, GET /api/audit/export) -- for pulling this history into an external SIEM (Splunk, Datadog, ...)"
            className="ml-auto rounded-md border border-border px-4 py-2 text-sm text-gray-300 disabled:opacity-50"
          >
            Export (NDJSON)
          </button>
        </div>
      </form>

      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      <div className="card p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-medium text-white">
            {total} entr{total === 1 ? "y" : "ies"}
          </h2>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <span>
              page {page} of {totalPages}
            </span>
            <button
              type="button"
              disabled={loading || page <= 1}
              onClick={() => runQuery(page - 1)}
              className="rounded-md border border-border px-2 py-1 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              type="button"
              disabled={loading || page >= totalPages}
              onClick={() => runQuery(page + 1)}
              className="rounded-md border border-border px-2 py-1 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>

        {entries.length === 0 ? (
          <p className="text-sm text-gray-500">No audit log entries match this filter.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>Method</TableHead>
                <TableHead>Path</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Request ID</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell className="whitespace-nowrap text-gray-400">
                    {new Date(entry.ts).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-white">{entry.actor}</TableCell>
                  <TableCell>
                    <span className="rounded bg-white/5 px-1.5 py-0.5 text-xs text-gray-300">
                      {entry.method}
                    </span>
                  </TableCell>
                  <TableCell className="break-all text-gray-300">{entry.path}</TableCell>
                  <TableCell
                    className={
                      entry.status >= 400 ? "font-medium text-red-400" : "text-emerald-400"
                    }
                  >
                    {entry.status}
                  </TableCell>
                  <TableCell className="whitespace-nowrap font-mono text-xs text-gray-500">
                    {entry.requestId}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </div>
  );
}
