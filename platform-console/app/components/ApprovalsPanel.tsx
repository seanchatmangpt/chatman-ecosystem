"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { ApprovalRequest } from "@/lib/approval-workflow";

// Re-declared here as `import type` only (never a runtime import) --
// lib/approval-workflow.ts pulls in lib/k8s.ts (fs/https), which must
// never end up in the client bundle. Same discipline
// components/BudgetAlertsPanel.tsx and components/WebhooksPanel.tsx
// already document.

function statusBadgeClass(status: ApprovalRequest["status"]): string {
  if (status === "approved") return "border-emerald-900 bg-emerald-950/40 text-emerald-300";
  if (status === "rejected") return "border-red-900 bg-red-950/40 text-red-300";
  return "border-amber-900 bg-amber-950/40 text-amber-300";
}

/**
 * Real per-action payload rendering: `quota.override` and
 * `tier.downgrade` both now carry a real `resourcePayload` (see
 * lib/approval-workflow.ts's ApprovalResourcePayload) an approver needs
 * to actually see before signing off -- the exact requested
 * `spec.hard` map, or the exact tier the org would move to -- instead of
 * the generic "confirm this action" `org.delete` gets by default (no
 * payload at all: its risk is fully described by action + targetId
 * alone).
 */
function PayloadDetail({ approval }: { approval: ApprovalRequest }) {
  const payload = approval.resourcePayload;
  if (!payload) return null;

  if (approval.action === "quota.override" && payload.requestedHard) {
    const entries = Object.entries(payload.requestedHard);
    return (
      <table className="mt-1 w-full max-w-xs text-xs text-gray-400">
        <tbody>
          {entries.map(([key, value]) => (
            <tr key={key}>
              <td className="pr-3 font-mono text-gray-500">{key}</td>
              <td className="font-mono text-gray-200">{value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  if (approval.action === "tier.downgrade" && payload.requestedTier) {
    return (
      <p className="mt-1 text-xs text-gray-400">
        requested tier: <span className="font-mono text-gray-200">{payload.requestedTier}</span>
      </p>
    );
  }

  return null;
}

/**
 * Real maker-checker approvals UI: lists every pending/recent
 * ApprovalRequest from GET /api/approvals and lets an owner-role identity
 * approve or reject a pending one via POST /api/approvals/[id]. No
 * client-side simulation of "approved" -- a row only changes state after
 * a real 200 from the API route (router.refresh() re-reads the live
 * ConfigMap), same "no optimistic UI" convention BudgetAlertsPanel and
 * OrgRolesPanel already follow. A 403 from the API (the requester trying
 * to approve their own request) is surfaced verbatim, not silently
 * retried or hidden.
 */
export default function ApprovalsPanel({
  approvals,
  currentIdentifier,
}: {
  approvals: ApprovalRequest[];
  currentIdentifier: string;
}) {
  const router = useRouter();
  const [decidingId, setDecidingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onDecide(requestId: string, decision: "approved" | "rejected") {
    if (
      !confirm(
        `${decision === "approved" ? "Approve" : "Reject"} this request? This cannot be undone.`,
      )
    ) {
      return;
    }
    setDecidingId(requestId);
    setError(null);
    try {
      const res = await fetch(`/api/approvals/${requestId}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ decision }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setDecidingId(null);
    }
  }

  return (
    <div className="space-y-4">
      {error && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {approvals.length === 0 && (
        <p className="text-sm text-gray-500">No approval requests yet.</p>
      )}

      <div className="overflow-x-auto rounded-md border border-gray-800">
        <table className="min-w-full divide-y divide-gray-800 text-sm">
          <thead className="bg-gray-900/60 text-left text-gray-400">
            <tr>
              <th className="px-4 py-2 font-medium">Action</th>
              <th className="px-4 py-2 font-medium">Target</th>
              <th className="px-4 py-2 font-medium">Requested By</th>
              <th className="px-4 py-2 font-medium">Requested At</th>
              <th className="px-4 py-2 font-medium">Status</th>
              <th className="px-4 py-2 font-medium">Decided By</th>
              <th className="px-4 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {approvals.map((a) => {
              const isSelfRequest = a.requestedBy === currentIdentifier;
              return (
                <tr key={a.requestId}>
                  <td className="px-4 py-2 font-mono text-gray-200">
                    {a.action}
                    <PayloadDetail approval={a} />
                  </td>
                  <td className="px-4 py-2 font-mono text-gray-400">{a.targetId}</td>
                  <td className="px-4 py-2 text-gray-300">{a.requestedBy}</td>
                  <td className="px-4 py-2 text-gray-500">
                    {new Date(a.requestedAt).toLocaleString()}
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={`rounded-full border px-2 py-0.5 text-xs ${statusBadgeClass(a.status)}`}
                    >
                      {a.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-gray-400">{a.approvedBy ?? "—"}</td>
                  <td className="px-4 py-2 text-right">
                    {a.status === "pending" && (
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => onDecide(a.requestId, "approved")}
                          disabled={decidingId === a.requestId || isSelfRequest}
                          title={
                            isSelfRequest
                              ? "You filed this request -- a second, distinct owner must approve it"
                              : undefined
                          }
                          className="rounded-md border border-emerald-800 bg-emerald-950/40 px-3 py-1 text-xs text-emerald-300 hover:bg-emerald-950/70 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => onDecide(a.requestId, "rejected")}
                          disabled={decidingId === a.requestId || isSelfRequest}
                          title={
                            isSelfRequest
                              ? "You filed this request -- a second, distinct owner must decide it"
                              : undefined
                          }
                          className="rounded-md border border-red-800 bg-red-950/40 px-3 py-1 text-xs text-red-300 hover:bg-red-950/70 disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
