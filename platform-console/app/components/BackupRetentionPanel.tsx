"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

// Re-declared as a plain local interface (never a runtime import of
// lib/backup-retention.ts, which pulls in lib/k8s.ts's fs/https) -- same
// client/server bundle-boundary discipline components/ApprovalsPanel.tsx
// and components/BudgetAlertsPanel.tsx already document.
interface BackupRecordView {
  id: string;
  jobName: string;
  projectName: string;
  takenAt: string;
  sizeBytes: number;
  retainUntil: string;
  status: "pending" | "running" | "completed" | "failed" | "expired";
  ageDays: number;
  daysUntilExpiry: number;
}

function statusBadgeClass(status: BackupRecordView["status"]): string {
  if (status === "completed") return "border-emerald-900 bg-emerald-950/40 text-emerald-300";
  if (status === "failed" || status === "expired") return "border-red-900 bg-red-950/40 text-red-300";
  return "border-amber-900 bg-amber-950/40 text-amber-300";
}

function formatBytes(bytes: number): string {
  if (bytes <= 0) return "-- (pending)";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(1)} ${units[i]}`;
}

/**
 * Real backup-history table + retention-policy selector for one org --
 * both real GET/PUT calls against app/api/orgs/[id]/backups and
 * app/api/orgs/[id]/backup-policy (lib/backup-retention.ts), never
 * fabricated rows. The retention selector's PUT is maker-checker gated
 * (lib/approval-workflow.ts's `backup.retention.change`): a 202 here
 * means a second, distinct owner must approve via /api/approvals before
 * the change actually applies -- this panel surfaces that pending state
 * rather than pretending the change already took effect.
 */
export default function BackupRetentionPanel({
  orgId,
  canManage,
  initialTier,
  initialRetentionDays,
  initialAllowedRange,
  initialBackups,
}: {
  orgId: string;
  canManage: boolean;
  initialTier: string;
  initialRetentionDays: number;
  initialAllowedRange: { minDays: number; maxDays: number };
  initialBackups: BackupRecordView[];
}) {
  const router = useRouter();
  const [retentionInput, setRetentionInput] = useState(String(initialRetentionDays));
  const [saving, setSaving] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runningBackup, setRunningBackup] = useState(false);
  const [backupProjectName, setBackupProjectName] = useState("");

  async function onSaveRetention() {
    setSaving(true);
    setError(null);
    setPendingMessage(null);
    try {
      const days = Number.parseInt(retentionInput, 10);
      const res = await fetch(`/api/orgs/${orgId}/backup-policy`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ retentionDays: days }),
      });
      const body = await res.json();
      if (res.status === 202) {
        setPendingMessage(body.message ?? "retention change is pending a second approver");
        return;
      }
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function onRunBackup() {
    if (!backupProjectName.trim()) {
      setError("enter a project name to back up");
      return;
    }
    setRunningBackup(true);
    setError(null);
    try {
      const res = await fetch(`/api/orgs/${orgId}/backups`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ projectName: backupProjectName.trim() }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setBackupProjectName("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunningBackup(false);
    }
  }

  return (
    <div className="space-y-8">
      <section className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-4">
        <h2 className="mb-1 text-sm font-medium text-white">Retention policy</h2>
        <p className="mb-3 text-xs text-gray-400">
          Current tier: <code>{initialTier}</code> -- allowed range: {initialAllowedRange.minDays} to{" "}
          {initialAllowedRange.maxDays} days.
        </p>

        {canManage ? (
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="number"
              min={initialAllowedRange.minDays}
              max={initialAllowedRange.maxDays}
              value={retentionInput}
              onChange={(e) => setRetentionInput(e.target.value)}
              className="w-28 rounded-md border border-gray-700 bg-gray-950 px-3 py-1.5 text-sm text-white"
            />
            <span className="text-xs text-gray-400">days</span>
            <button
              onClick={onSaveRetention}
              disabled={saving}
              className="rounded-md border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save retention"}
            </button>
          </div>
        ) : (
          <p className="text-xs text-gray-500">Only an org owner can change the retention window.</p>
        )}

        {pendingMessage && (
          <p className="mt-3 rounded-md border border-amber-900 bg-amber-950/40 px-3 py-2 text-xs text-amber-300">
            {pendingMessage}
          </p>
        )}
        {error && (
          <p className="mt-3 rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
            {error}
          </p>
        )}
      </section>

      {canManage && (
        <section className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-4">
          <h2 className="mb-2 text-sm font-medium text-white">Run a backup now</h2>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="text"
              placeholder="project name"
              value={backupProjectName}
              onChange={(e) => setBackupProjectName(e.target.value)}
              className="w-56 rounded-md border border-gray-700 bg-gray-950 px-3 py-1.5 text-sm text-white"
            />
            <button
              onClick={onRunBackup}
              disabled={runningBackup}
              className="rounded-md border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
            >
              {runningBackup ? "Starting..." : "Run backup"}
            </button>
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-2 text-sm font-medium text-white">Backup history</h2>
        {initialBackups.length === 0 ? (
          <p className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-400">
            No backups recorded for this org yet.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-md border border-gray-800">
            <table className="min-w-full divide-y divide-gray-800 text-sm">
              <thead className="bg-gray-900/60 text-left text-gray-400">
                <tr>
                  <th className="px-4 py-2 font-medium">Project</th>
                  <th className="px-4 py-2 font-medium">Taken</th>
                  <th className="px-4 py-2 font-medium">Age</th>
                  <th className="px-4 py-2 font-medium">Size</th>
                  <th className="px-4 py-2 font-medium">Expires</th>
                  <th className="px-4 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {initialBackups.map((b) => (
                  <tr key={b.id} className="text-gray-200">
                    <td className="px-4 py-2">{b.projectName}</td>
                    <td className="px-4 py-2 text-gray-400">{new Date(b.takenAt).toLocaleString()}</td>
                    <td className="px-4 py-2 text-gray-400">{b.ageDays}d</td>
                    <td className="px-4 py-2 text-gray-400">{formatBytes(b.sizeBytes)}</td>
                    <td className="px-4 py-2 text-gray-400">
                      {b.daysUntilExpiry >= 0 ? `${b.daysUntilExpiry}d left` : "expired"}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={`rounded-full border px-2 py-0.5 text-xs ${statusBadgeClass(b.status)}`}
                      >
                        {b.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
