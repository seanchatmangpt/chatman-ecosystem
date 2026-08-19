import { cookies } from "next/headers";
import Nav from "@/components/Nav";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";
import { requireRole } from "@/lib/authz";
import { getPartner, listPartnerCommissions } from "@/lib/partners";

export const dynamic = "force-dynamic";

// Owner-only page (same boundary as /audit and the Partner routes'
// server-side `requirePlatformAdmin`): the real, immutable commission
// ledger -- one persisted row per (partner, period) in
// platform_console.partner_commissions -- a partner's finance/procurement
// team audits payouts against before signing a channel agreement. This
// page reads lib/partners.ts directly (same "page renders, the route's
// own server-side check is the real enforcement boundary" convention
// app/audit/page.tsx's header comment already documents); the underlying
// enforcement for the data itself is GET
// /api/partners/[partnerId]/commissions's own requirePlatformAdmin call.
export default async function PartnerCommissionsPage({
  params,
}: {
  params: Promise<{ partnerId: string }>;
}) {
  const { partnerId } = await params;
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

  const access = await requireRole(session, "owner");
  if (!access.ok) {
    return (
      <>
        <Nav />
        <main className="mx-auto max-w-3xl px-6 py-10">
          <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            forbidden -- role &apos;{access.role}&apos; does not have platform-admin access
          </p>
        </main>
      </>
    );
  }

  const partnerResult = await getPartner(partnerId);
  const partner = partnerResult.ok ? partnerResult.data : null;
  const commissionsResult = await listPartnerCommissions(partnerId);
  const commissions = commissionsResult.ok ? commissionsResult.data : [];

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">
          Commission Ledger{partner ? ` -- ${partner.name}` : ""}
        </h1>
        <p className="mb-8 max-w-3xl text-sm text-gray-400">
          Real, immutable per-period commission rows computed off this partner&apos;s actual
          managed-org spend (<code>platform_console.partner_commissions</code>) -- the standard
          AWS/Azure/GCP partner-program shape: a recurring percentage-of-managed-spend commission,
          distinct from the one-time referral-signup credit ledger. Compute and persist only; no
          Stripe payout automation runs from this page.
        </p>

        {!partnerResult.ok && (
          <p className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {partnerResult.error}
          </p>
        )}
        {partnerResult.ok && !partner && (
          <p className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            partner not found
          </p>
        )}
        {partner && partner.commissionRatePct === undefined && (
          <p className="mb-6 rounded-md border border-yellow-900 bg-yellow-950/30 px-4 py-3 text-sm text-yellow-300">
            No <code>commissionRatePct</code> set on this partner -- commission cannot be computed
            until a rate is configured.
          </p>
        )}
        {partner?.commissionRatePct !== undefined && (
          <p className="mb-6 text-sm text-gray-400">
            Commission rate: <span className="text-white">{partner.commissionRatePct}%</span> of
            monthly managed-org spend.
          </p>
        )}

        {!commissionsResult.ok && (
          <p className="mb-6 rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {commissionsResult.error}
          </p>
        )}

        <div className="overflow-x-auto rounded-md border border-gray-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-900 text-gray-400">
              <tr>
                <th className="px-4 py-2 font-medium">Period</th>
                <th className="px-4 py-2 font-medium">Rate</th>
                <th className="px-4 py-2 font-medium">Managed spend</th>
                <th className="px-4 py-2 font-medium">Commission owed</th>
                <th className="px-4 py-2 font-medium">Computed at</th>
              </tr>
            </thead>
            <tbody>
              {commissions.length === 0 ? (
                <tr>
                  <td className="px-4 py-4 text-gray-500" colSpan={5}>
                    No commission periods computed yet for this partner.
                  </td>
                </tr>
              ) : (
                commissions.map((c) => (
                  <tr key={c.period} className="border-t border-gray-800">
                    <td className="px-4 py-2 text-white">{c.period}</td>
                    <td className="px-4 py-2 text-gray-300">{c.commissionRatePct}%</td>
                    <td className="px-4 py-2 text-gray-300">${c.totalManagedSpendUsd.toFixed(2)}</td>
                    <td className="px-4 py-2 text-white">${c.commissionOwedUsd.toFixed(2)}</td>
                    <td className="px-4 py-2 text-gray-500">{c.computedAt}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
