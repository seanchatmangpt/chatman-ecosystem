"use client";

import { useCallback, useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Nav from "@/components/Nav";

type Role = "viewer" | "member" | "owner";
type InviteStatus = "pending" | "accepted" | "revoked";

interface OrgInvite {
  token: string;
  email: string;
  role: Role;
  invitedBy: string;
  invitedAt: string;
  expiresAt: string;
  status: InviteStatus;
}

interface SeatsSummary {
  tier: "starter" | "pro" | "enterprise";
  limit: number;
  used: number;
  accepted: number;
  pending: number;
}

const ROLES: Role[] = ["viewer", "member", "owner"];

// Real seat-based user management page: same page shape as
// app/org/branding/page.tsx and app/org/security/page.tsx (query-param
// `?orgId=`, owner-only, the API route -- not this page -- is the real
// enforcement boundary). Shows the seat-usage meter (used/limit from
// SEAT_LIMITS, lib/tiers.ts), an invite form, and a pending/accepted/
// revoked table backed by POST/GET/DELETE /api/orgs/[id]/invites(/[id]).
function OrgSeatsPageInner() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";

  const [seats, setSeats] = useState<SeatsSummary | null>(null);
  const [invites, setInvites] = useState<OrgInvite[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("member");
  const [loading, setLoading] = useState(false);
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = useCallback(() => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(orgId)}/invites`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        setSeats(body.seats);
        setInvites(body.invites);
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [orgId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleInvite(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId) return;
    setInviting(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/invites`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, role }),
      });
      const body = await res.json();
      if (!res.ok) {
        if (body.seats) {
          setSeats(body.seats);
        }
        throw new Error(body.reason ?? body.error ?? `request failed (${res.status})`);
      }
      setNotice(`Invited ${email}.`);
      setEmail("");
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setInviting(false);
    }
  }

  async function handleRevoke(token: string) {
    if (!orgId) return;
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(
        `/api/orgs/${encodeURIComponent(orgId)}/invites/${encodeURIComponent(token)}`,
        { method: "DELETE" },
      );
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const pct = seats && seats.limit > 0 ? Math.min(100, (seats.used / seats.limit) * 100) : 0;
  const atLimit = seats ? seats.used >= seats.limit : false;

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Seats</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real per-tier seat cap (Vercel/Retool/Auth0 pattern): accepted members plus still-open
          pending invites both count against <code>SEAT_LIMITS[tier]</code>. Backed by
          <code> invite-&lt;token&gt;</code> entries in the same
          <code> platform-console-org-roles</code> ConfigMap this org&apos;s role assignments
          already live in. Enforced server-side by <code>POST /api/orgs/[id]/invites</code>, not
          just this page.
        </p>

        {!orgId && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            Append <code>?orgId=&lt;org id&gt;</code> to this page&apos;s URL to manage that
            org&apos;s seats (org ids are returned by <code>POST /api/orgs</code> and listed by{" "}
            <code>GET /api/orgs</code>, owner-only).
          </div>
        )}

        {orgId && (
          <>
            {loading && !seats && <p className="text-sm text-gray-400">loading seat usage...</p>}

            {seats && (
              <div className="mb-8 rounded-md border border-gray-800 bg-gray-950 px-4 py-4">
                <div className="mb-2 flex items-baseline justify-between">
                  <span className="text-sm font-medium text-gray-300">
                    {seats.used} / {seats.limit} seats used
                  </span>
                  <span className="text-xs uppercase tracking-wide text-gray-500">
                    {seats.tier} tier
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800">
                  <div
                    className={`h-full rounded-full ${atLimit ? "bg-red-500" : "bg-indigo-500"}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  {seats.accepted} accepted member{seats.accepted === 1 ? "" : "s"},{" "}
                  {seats.pending} pending invite{seats.pending === 1 ? "" : "s"}.
                </p>
              </div>
            )}

            <form onSubmit={handleInvite} className="mb-10 space-y-4">
              <div className="flex gap-3">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="new-hire@acme.com"
                  className="flex-1 rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                />
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as Role)}
                  className="rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
                <button
                  type="submit"
                  disabled={inviting || (seats ? seats.used >= seats.limit : false)}
                  className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  {inviting ? "Inviting..." : "Invite"}
                </button>
              </div>
              {seats && seats.used >= seats.limit && (
                <p className="text-xs text-amber-400">
                  Seat limit reached for the {seats.tier} tier ({seats.limit} seats). Upgrade the
                  plan to invite more people.
                </p>
              )}
            </form>

            {error && (
              <p className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                {error}
              </p>
            )}
            {notice && !error && (
              <p className="mb-6 rounded-md border border-emerald-900 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-300">
                {notice}
              </p>
            )}

            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-gray-800 text-xs uppercase tracking-wide text-gray-500">
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Role</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2 pr-4">Invited</th>
                  <th className="py-2 pr-4">Expires</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {invites.map((invite) => (
                  <tr key={invite.token} className="border-b border-gray-900 text-gray-300">
                    <td className="py-2 pr-4">{invite.email}</td>
                    <td className="py-2 pr-4">{invite.role}</td>
                    <td className="py-2 pr-4">
                      <span
                        className={
                          invite.status === "accepted"
                            ? "text-emerald-400"
                            : invite.status === "revoked"
                              ? "text-gray-500"
                              : "text-amber-400"
                        }
                      >
                        {invite.status}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-gray-500">
                      {new Date(invite.invitedAt).toLocaleDateString()}
                    </td>
                    <td className="py-2 pr-4 text-gray-500">
                      {new Date(invite.expiresAt).toLocaleDateString()}
                    </td>
                    <td className="py-2">
                      {invite.status === "pending" && (
                        <button
                          onClick={() => handleRevoke(invite.token)}
                          className="text-xs text-red-400 hover:text-red-300"
                        >
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
                {invites.length === 0 && !loading && (
                  <tr>
                    <td colSpan={6} className="py-4 text-center text-gray-500">
                      No invites yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </>
        )}
      </main>
    </>
  );
}

export default function OrgSeatsPage() {
  return (
    <Suspense fallback={null}>
      <OrgSeatsPageInner />
    </Suspense>
  );
}
