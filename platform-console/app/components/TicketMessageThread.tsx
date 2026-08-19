"use client";

import { useEffect, useState, type FormEvent } from "react";

// Real threaded ticket-message UI -- polls GET
// /api/orgs/[id]/tickets/[ticketId]/messages (same standalone-panel,
// self-fetching convention as components/SpendHistoryChart.tsx) and
// posts new messages through the same route's POST, refetching the
// thread on success rather than reaching for websockets/live-chat
// infra, matching what's realistically buildable on this console's
// existing async-only storage.

type SupportTicketMessageAuthorType = "customer" | "support";
type SupportTicketStatus = "open" | "responded" | "resolved" | "breached";

interface SupportTicketMessage {
  id: string;
  ticketId: string;
  authorType: SupportTicketMessageAuthorType;
  authorId: string;
  body: string;
  createdAt: string;
}

const POLL_INTERVAL_MS = 8000;

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString();
}

export default function TicketMessageThread({
  orgId,
  ticketId,
  onTicketStatusChange,
}: {
  orgId: string;
  ticketId: string;
  onTicketStatusChange?: (status: SupportTicketStatus) => void;
}) {
  const [messages, setMessages] = useState<SupportTicketMessage[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const res = await fetch(`/api/orgs/${orgId}/tickets/${ticketId}/messages`, {
          cache: "no-store",
        });
        const payload = await res.json();
        if (cancelled) return;
        if (!res.ok) {
          setError(payload?.error ?? `request failed (${res.status})`);
          return;
        }
        setError(null);
        setMessages(payload.messages as SupportTicketMessage[]);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      }
    }

    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [orgId, ticketId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const body = draft.trim();
    if (!body || sending) return;
    setSending(true);
    setError(null);
    try {
      const res = await fetch(`/api/orgs/${orgId}/tickets/${ticketId}/messages`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ body }),
      });
      const payload = await res.json();
      if (!res.ok) {
        setError(payload?.error ?? `request failed (${res.status})`);
        return;
      }
      setDraft("");
      if (payload.ticket?.status) onTicketStatusChange?.(payload.ticket.status as SupportTicketStatus);
      const refreshed = await fetch(`/api/orgs/${orgId}/tickets/${ticketId}/messages`, {
        cache: "no-store",
      });
      const refreshedPayload = await refreshed.json();
      if (refreshed.ok) setMessages(refreshedPayload.messages as SupportTicketMessage[]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="rounded-md border border-gray-800 bg-gray-900/20 p-5">
      <h3 className="mb-3 text-sm font-semibold text-white">Conversation</h3>

      {error && (
        <p className="mb-3 rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      {messages === null && !error && <p className="text-xs text-gray-500">Loading thread...</p>}

      {messages !== null && messages.length === 0 && (
        <p className="text-xs text-gray-500">No messages yet.</p>
      )}

      {messages !== null && messages.length > 0 && (
        <ul className="mb-4 space-y-3">
          {messages.map((message) => (
            <li
              key={message.id}
              className={`rounded-md border px-4 py-3 text-sm ${
                message.authorType === "support"
                  ? "border-blue-900 bg-blue-950/30"
                  : "border-gray-800 bg-gray-900/40"
              }`}
            >
              <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
                <span className="font-medium text-gray-300">
                  {message.authorType === "support" ? "Support" : "Customer"} -- {message.authorId}
                </span>
                <span>{formatTimestamp(message.createdAt)}</span>
              </div>
              <p className="whitespace-pre-wrap text-gray-200">{message.body}</p>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Write a reply..."
          rows={3}
          className="w-full rounded-md border border-gray-800 bg-gray-950 px-3 py-2 text-sm text-gray-200 placeholder:text-gray-600 focus:border-gray-600 focus:outline-none"
        />
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={sending || !draft.trim()}
            className="rounded-md bg-white px-4 py-2 text-xs font-medium text-black disabled:cursor-not-allowed disabled:opacity-40"
          >
            {sending ? "Sending..." : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}
