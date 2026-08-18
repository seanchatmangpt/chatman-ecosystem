"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { ActiveSessionRecord } from "@/lib/active-sessions";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

/**
 * Real list + revoke client for GET/DELETE /api/sessions ->
 * lib/active-sessions.ts's listActiveSessions/revokeSession against the
 * live platform_console.active_sessions table. No client-side simulation
 * of "revoked" -- a row only flips after a real 200 from the API route
 * (router.refresh() re-reads the live table server-side), same
 * "no optimistic UI" convention AuditLogPanel/ApiKeysPanel already follow.
 */
export default function SessionsPanel({
  initialSessions,
  currentSessionId,
}: {
  initialSessions: ActiveSessionRecord[];
  currentSessionId: string | null;
}) {
  const router = useRouter();
  const [sessions, setSessions] = useState(initialSessions);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onRefresh() {
    setError(null);
    try {
      const res = await fetch("/api/sessions");
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSessions(body.sessions as ActiveSessionRecord[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function onRevoke(sessionId: string) {
    const isSelf = sessionId === currentSessionId;
    const confirmMessage = isSelf
      ? "This is YOUR OWN current session. Revoking it will log you out immediately on your next request. Continue?"
      : "Revoke this session? Its cookie will start getting a real 401 immediately, before its own expiry.";
    if (!confirm(confirmMessage)) return;

    setRevokingId(sessionId);
    setError(null);
    try {
      const res = await fetch(`/api/sessions?sessionId=${encodeURIComponent(sessionId)}`, {
        method: "DELETE",
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
      await onRefresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRevokingId(null);
    }
  }

  const sorted = [...sessions].sort((a, b) => b.lastSeenAt.localeCompare(a.lastSeenAt));

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-medium text-white">
            {sorted.length} session{sorted.length === 1 ? "" : "s"}
          </h2>
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-300 hover:text-white"
          >
            Refresh
          </button>
        </div>

        {sorted.length === 0 ? (
          <p className="text-sm text-gray-500">No sessions recorded yet.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Identifier</TableHead>
                <TableHead>Provider</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Last seen</TableHead>
                <TableHead>IP</TableHead>
                <TableHead>Status</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {sorted.map((s) => (
                <TableRow key={s.sessionId}>
                  <TableCell className="text-white">
                    {s.identifier}
                    {s.sessionId === currentSessionId && (
                      <span className="ml-2 rounded bg-accent/20 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-accent">
                        this session
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    <span className="rounded bg-white/5 px-1.5 py-0.5 text-xs text-gray-300">
                      {s.authProvider}
                    </span>
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-gray-400">
                    {new Date(s.createdAt).toLocaleString()}
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-gray-400">
                    {new Date(s.lastSeenAt).toLocaleString()}
                  </TableCell>
                  <TableCell className="whitespace-nowrap text-xs text-gray-500">
                    {s.ip ?? "-"}
                  </TableCell>
                  <TableCell>
                    {s.revoked ? (
                      <span className="text-xs text-red-400">
                        revoked {s.revokedAt ? `at ${new Date(s.revokedAt).toLocaleString()}` : ""}
                        {s.revokedBy ? ` by ${s.revokedBy}` : ""}
                      </span>
                    ) : (
                      <span className="text-xs text-emerald-400">active</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {!s.revoked && (
                      <button
                        type="button"
                        onClick={() => onRevoke(s.sessionId)}
                        disabled={revokingId === s.sessionId}
                        className="rounded-md border border-red-900 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
                      >
                        {revokingId === s.sessionId ? "Revoking..." : "Revoke"}
                      </button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
