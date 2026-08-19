import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import TicketMessageThread from "@/components/TicketMessageThread";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRoleIn } from "@/lib/authz";
import { getOrg } from "@/lib/orgs";
import { getSupportTicket } from "@/lib/support-tickets";

export const dynamic = "force-dynamic";

// Real ticket-detail page: the piece missing between lib/support-tickets.ts's
// SLA-timer status field and an actual operable support workflow -- see
// that module's own header comment. Renders the ticket's own fixed
// fields (subject/body/priority/status/SLA due-by) plus
// TicketMessageThread, the client component that owns polling
// GET/POST /api/orgs/[id]/tickets/[ticketId]/messages. Gated the same
// server-side requireRoleIn(viewer) floor as every other /orgs/[id]/*
// page in this app (see app/orgs/[id]/billing/page.tsx's own header
// comment for the identical reasoning) -- re-checked independently by
// the messages route handler regardless of what this page renders.

const STATUS_STYLES: Record<string, string> = {
  open: "border-amber-900 bg-amber-950/40 text-amber-300",
  responded: "border-blue-900 bg-blue-950/40 text-blue-300",
  resolved: "border-emerald-900 bg-emerald-950/40 text-emerald-300",
  breached: "border-red-900 bg-red-950/40 text-red-300",
};

export default async function TicketDetailPage({
  params,
}: {
  params: Promise<{ id: string; ticketId: string }>;
}) {
  const { id, ticketId } = await params;
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  if (!session) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            unauthenticated
          </p>
        </main>
      </>
    );
  }

  const orgResult = await getOrg(id);
  if (!orgResult.ok || !orgResult.data) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {orgResult.ok ? "org not found" : orgResult.error}
          </p>
        </main>
      </>
    );
  }
  const org = orgResult.data;

  const viewerAccess = await requireRoleIn(session, org.namespace, "viewer");

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Support ticket</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          {org.name} -- real message thread against this ticket, with every post logged through
          the audit trail.
        </p>

        {!viewerAccess.ok && (
          <div className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            <p className="font-medium">403 -- forbidden</p>
            <p className="mt-1 text-red-300/80">
              Your role (<code>{viewerAccess.role}</code>) does not meet the required minimum role
              (<code>viewer</code>) to view this ticket.
            </p>
          </div>
        )}

        {viewerAccess.ok && <TicketDetail orgId={id} ticketId={ticketId} />}
      </main>
    </>
  );
}

async function TicketDetail({ orgId, ticketId }: { orgId: string; ticketId: string }) {
  const ticketResult = await getSupportTicket(orgId, ticketId);

  if (!ticketResult.ok) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        {ticketResult.error}
      </p>
    );
  }
  if (!ticketResult.data) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        ticket not found
      </p>
    );
  }

  const ticket = ticketResult.data;
  const statusStyle = STATUS_STYLES[ticket.status] ?? "border-gray-800 bg-gray-900/40 text-gray-300";

  return (
    <div className="space-y-6">
      <div className="rounded-md border border-gray-800 bg-gray-900/20 p-5">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <h2 className="text-lg font-semibold text-white">{ticket.subject}</h2>
          <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${statusStyle}`}>
            {ticket.status}
          </span>
          <span className="rounded-full border border-gray-800 bg-gray-900/40 px-2 py-0.5 text-xs text-gray-400">
            {ticket.priority}
          </span>
        </div>
        <p className="mb-4 whitespace-pre-wrap text-sm text-gray-300">{ticket.body}</p>
        <dl className="grid grid-cols-2 gap-3 text-xs text-gray-500 sm:grid-cols-4">
          <div>
            <dt className="uppercase tracking-wide">Created</dt>
            <dd className="mt-1 text-gray-300">{new Date(ticket.createdAt).toLocaleString()}</dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide">First response due</dt>
            <dd className="mt-1 text-gray-300">
              {new Date(ticket.firstResponseDueAt).toLocaleString()}
            </dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide">First responded</dt>
            <dd className="mt-1 text-gray-300">
              {ticket.firstRespondedAt ? new Date(ticket.firstRespondedAt).toLocaleString() : "--"}
            </dd>
          </div>
          <div>
            <dt className="uppercase tracking-wide">Resolved</dt>
            <dd className="mt-1 text-gray-300">
              {ticket.resolvedAt ? new Date(ticket.resolvedAt).toLocaleString() : "--"}
            </dd>
          </div>
        </dl>
      </div>

      <TicketMessageThread orgId={orgId} ticketId={ticketId} />
    </div>
  );
}
