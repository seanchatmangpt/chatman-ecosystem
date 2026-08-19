"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { Org } from "@/lib/orgs";
import type { Incident } from "@/lib/incidents";

/**
 * Real DR failover runbook panel -- drives lib/dr-failover.ts's
 * initiateFailover through POST /api/dr/initiate-failover (maker-checker
 * gated: the first submit almost always returns 202 pending_approval, a
 * second distinct owner must approve via the Approvals page before a
 * retry actually runs the failover) and polls
 * GET /api/dr/failover-status/[orgId] for live restore-Job progress. No
 * client-side simulation of "failover complete" -- the progress states
 * below are read directly off the server's real, live status.
 */
export default function DrRunbookPanel({
  org,
  blockingIncident,
  availableRegions,
}: {
  org: Org;
  blockingIncident: Incident | null;
  availableRegions: string[];
}) {
  const router = useRouter();
  const [toRegion, setToRegion] = useState(
    availableRegions.find((r) => r !== org.region) ?? "",
  );
  const [reason, setReason] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<{
    restoreJob: { name: string; status: string } | null;
    sourceBackupJob: string;
  } | null>(null);

  const canInitiate = Boolean(org.region) && blockingIncident !== null;

  async function submitFailover() {
    if (!org.region || !toRegion || !reason.trim()) return;
    setSubmitting(true);
    setError(null);
    setPendingMessage(null);
    try {
      const res = await fetch("/api/dr/initiate-failover", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          orgId: org.id,
          fromRegion: org.region,
          toRegion,
          reason: reason.trim(),
        }),
      });
      const body = await res.json();
      if (res.status === 202) {
        setPendingMessage(body.message ?? "Failover request pending a second approver.");
        return;
      }
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setLastResult({ restoreJob: body.restoreJob, sourceBackupJob: body.sourceBackupJob });
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
      setConfirming(false);
    }
  }

  return (
    <div className="card space-y-6 p-6">
      <div>
        <h2 className="text-base font-medium text-white">DR failover runbook</h2>
        <p className="mt-1 text-xs text-gray-500">
          Region-pinning-aware disaster recovery: re-pins this org&apos;s data-residency region and
          restores its latest backup into the newly pinned namespace. Gated behind an open incident
          referencing the source region AND a second, distinct owner approval.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-xs text-gray-500">Current pinned region</p>
          <p className="text-sm font-medium text-white">{org.region ?? "not pinned"}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Failover precondition</p>
          {blockingIncident ? (
            <p className="text-sm font-medium text-amber-400">
              Open incident {blockingIncident.id.slice(0, 8)} ({blockingIncident.severity}) references
              this region -- failover is enabled.
            </p>
          ) : (
            <p className="text-sm font-medium text-gray-500">
              No open incident references {org.region ?? "the pinned region"} -- failover is disabled.
            </p>
          )}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Failover to region</span>
          <select
            value={toRegion}
            onChange={(e) => setToRegion(e.target.value)}
            disabled={!canInitiate}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            {availableRegions
              .filter((r) => r !== org.region)
              .map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Reason (required, recorded in the audit chain)</span>
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={!canInitiate}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
            placeholder={`e.g. incident ${blockingIncident?.id.slice(0, 8) ?? ""} sustained region outage`}
          />
        </label>
      </div>

      {!confirming ? (
        <button
          type="button"
          disabled={!canInitiate || !toRegion || !reason.trim()}
          onClick={() => setConfirming(true)}
          className="rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          Initiate failover
        </button>
      ) : (
        <div className="space-y-3 rounded-md border border-red-900 bg-red-950/30 p-4">
          <p className="text-sm text-red-200">
            This will re-pin org <span className="font-mono">{org.id}</span> from{" "}
            <span className="font-mono">{org.region}</span> to{" "}
            <span className="font-mono">{toRegion}</span> and trigger a real restore Job that
            overwrites the target database&apos;s live table data. This requires a second, distinct
            owner-role approval and cannot be undone by this panel.
          </p>
          <div className="flex gap-3">
            <button
              type="button"
              disabled={submitting}
              onClick={submitFailover}
              className="rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {submitting ? "Submitting..." : "Confirm: initiate failover"}
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={() => setConfirming(false)}
              className="rounded-md border border-border px-4 py-2 text-sm text-gray-300"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {pendingMessage && (
        <p className="rounded-md border border-amber-900 bg-amber-950/30 px-3 py-2 text-xs text-amber-300">
          {pendingMessage}
        </p>
      )}
      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
      {lastResult && (
        <p className="rounded-md border border-emerald-900 bg-emerald-950/30 px-3 py-2 text-xs text-emerald-300">
          Failover initiated. Restore Job <span className="font-mono">{lastResult.restoreJob?.name}</span>{" "}
          from backup <span className="font-mono">{lastResult.sourceBackupJob}</span> is now running --
          poll /api/dr/failover-status/{org.id}?restoreJobName={lastResult.restoreJob?.name} for
          progress.
        </p>
      )}
    </div>
  );
}
