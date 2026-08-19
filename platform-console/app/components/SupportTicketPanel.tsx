"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { SupportTicket, SupportTicketStatus } from "@/lib/support-tickets";

// Re-declared type imports only (`import type`, erased at compile time) --
// lib/support-tickets.ts pulls in lib/audit-db.ts (the `pg` driver, real
// Node.js net/tls core modules) and lib/orgs.ts (lib/k8s.ts), which must
// never end up in the client bundle. Same "type-only import from a
// server-only lib module" convention components/BudgetAlertsPanel.tsx and
// components/WebhooksPanel.tsx already use.

const STATUS_LABEL: Record<SupportTicketStatus, string> = {
  open: "Open",
  responded: "Responded",
  resolved: "Resolved",
  breached: "SLA breached",
};

const STATUS_CLASS: Record<SupportTicketStatus, string> = {
  open: "text-yellow-600",
  responded: "text-blue-600",
  resolved: "text-green-600",
  breached: "text-red-600 font-semibold",
};

function formatDue(ticket: SupportTicket): string {
  const due = new Date(ticket.firstResponseDueAt);
  return due.toLocaleString();
}

/**
 * Real support-ticket SLA-timer panel: reads/writes the real
 * `platform_console.support_tickets` table via
 * POST/PATCH /api/orgs/[id]/tickets(/[ticketId]) -> lib/support-tickets.ts.
 * No client-side simulation of "responded"/"resolved"/"breached" -- a row
 * only changes after a real 200/201 from the API route
 * (router.refresh() re-reads the live table server-side), same
 * "no optimistic UI" convention every other mutating panel in this
 * console follows (BudgetAlertsPanel, WebhooksPanel, OrgRolesPanel).
 * `canRespond` gates the Respond/Resolve controls -- the owner-only floor
 * PATCH /api/orgs/[id]/tickets/[ticketId] itself enforces server-side;
 * this only hides controls a non-owner's click would 403 on anyway.
 */
export default function SupportTicketPanel({
  orgId,
  tickets,
  canRespond,
}: {
  orgId: string;
  tickets: SupportTicket[];
  canRespond: boolean;
}) {
  const router = useRouter();
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [filing, setFiling] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onFile(e: React.FormEvent) {
    e.preventDefault();
    setFiling(true);
    setError(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/tickets`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ subject, body }),
      });
      const responseBody = await res.json();
      if (!res.ok) {
        setError(responseBody.error ?? `HTTP ${res.status}`);
        return;
      }
      setSubject("");
      setBody("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setFiling(false);
    }
  }

  async function onUpdate(ticketId: string, status: "responded" | "resolved") {
    setUpdatingId(ticketId);
    setError(null);
    try {
      const res = await fetch(
        `/api/orgs/${encodeURIComponent(orgId)}/tickets/${encodeURIComponent(ticketId)}`,
        {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ status }),
        },
      );
      const responseBody = await res.json();
      if (!res.ok) {
        setError(responseBody.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onFile} className="space-y-2 border rounded p-4">
        <h3 className="font-medium">File a support ticket</h3>
        <input
          type="text"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Subject"
          className="w-full border rounded px-2 py-1"
          required
        />
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          placeholder="Describe the issue"
          className="w-full border rounded px-2 py-1"
          rows={3}
          required
        />
        <button
          type="submit"
          disabled={filing}
          className="border rounded px-3 py-1 disabled:opacity-50"
        >
          {filing ? "Filing…" : "File ticket"}
        </button>
      </form>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="text-left border-b">
            <th className="py-1 pr-2">Subject</th>
            <th className="py-1 pr-2">Priority</th>
            <th className="py-1 pr-2">Status</th>
            <th className="py-1 pr-2">First response due</th>
            <th className="py-1 pr-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {tickets.length === 0 && (
            <tr>
              <td colSpan={5} className="py-2 text-gray-500">
                No support tickets filed yet.
              </td>
            </tr>
          )}
          {tickets.map((ticket) => (
            <tr key={ticket.id} className="border-b">
              <td className="py-1 pr-2">{ticket.subject}</td>
              <td className="py-1 pr-2">{ticket.priority}</td>
              <td className={`py-1 pr-2 ${STATUS_CLASS[ticket.status]}`}>
                {STATUS_LABEL[ticket.status]}
              </td>
              <td className="py-1 pr-2">{formatDue(ticket)}</td>
              <td className="py-1 pr-2 space-x-2">
                {canRespond && (ticket.status === "open" || ticket.status === "breached") && (
                  <button
                    onClick={() => onUpdate(ticket.id, "responded")}
                    disabled={updatingId === ticket.id}
                    className="border rounded px-2 py-0.5 disabled:opacity-50"
                  >
                    Respond
                  </button>
                )}
                {canRespond && ticket.status !== "resolved" && (
                  <button
                    onClick={() => onUpdate(ticket.id, "resolved")}
                    disabled={updatingId === ticket.id}
                    className="border rounded px-2 py-0.5 disabled:opacity-50"
                  >
                    Resolve
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
