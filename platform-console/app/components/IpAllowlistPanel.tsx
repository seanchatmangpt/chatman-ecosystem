"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * Reads/writes the real `platform-console-ip-allowlist` ConfigMap via
 * GET/PUT `/api/orgs/[id]/ip-allowlist` -> lib/ip-allowlist.ts. PUT is
 * owner-gated server-side (requireRole) -- this panel only ever renders
 * write controls after the server-rendered security page has already
 * confirmed the viewer is an owner, but the real enforcement boundary is
 * the route, not this component. No optimistic UI: a row only
 * disappears/appears after a real 200 from the route (`router.refresh()`
 * re-reads the live ConfigMap server-side), same convention
 * OrgRolesPanel/FeatureFlagsPanel already follow.
 *
 * `yourIp` (this request's own resolved IP, from clientIpFrom via the
 * route) is always shown, and is checked client-side against the entries
 * about to be saved before the save button is enabled -- purely a UX
 * guard against an admin locking themselves out, NOT itself an
 * authorization check (the real check is middleware.ts's
 * checkIpAllowed, evaluated fresh on the very next request either way).
 */

export interface IpAllowlistPanelProps {
  orgId: string;
  namespace: string;
  cidrs: string[];
  yourIp: string | null;
}

// Same real, dependency-free IPv4/CIDR containment check lib/ip-allowlist.ts
// exports server-side -- duplicated here (not imported) because this is a
// "use client" component and lib/ip-allowlist.ts pulls in lib/k8s.ts
// (Node-only fs/https), which cannot be bundled for the browser. Purely
// advisory client-side (see module doc above); the real enforcement stays
// server-side in middleware.ts, which calls the lib/ip-allowlist.ts
// original.
function parseCidrClient(cidr: string): { network: number; mask: number } | null {
  const trimmed = cidr.trim();
  const slashIndex = trimmed.indexOf("/");
  if (slashIndex === -1) return null;
  const addrPart = trimmed.slice(0, slashIndex);
  const prefixPart = trimmed.slice(slashIndex + 1);
  if (!/^\d{1,2}$/.test(prefixPart)) return null;
  const prefix = Number(prefixPart);
  if (prefix < 0 || prefix > 32) return null;
  const octets = addrPart.split(".");
  if (octets.length !== 4) return null;
  let addr = 0;
  for (const o of octets) {
    if (!/^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$/.test(o)) return null;
    addr = (addr << 8) | Number(o);
  }
  addr = addr >>> 0;
  const mask = prefix === 0 ? 0 : (0xffffffff << (32 - prefix)) >>> 0;
  return { network: (addr & mask) >>> 0, mask };
}

function ipMatchesAnyClient(ip: string, cidrs: string[]): boolean {
  const octets = ip.trim().split(".");
  if (octets.length !== 4) return false;
  let addr = 0;
  for (const o of octets) {
    if (!/^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)$/.test(o)) return false;
    addr = (addr << 8) | Number(o);
  }
  addr = addr >>> 0;
  return cidrs.some((cidr) => {
    const parsed = parseCidrClient(cidr);
    if (!parsed) return false;
    return ((addr & parsed.mask) >>> 0) === parsed.network;
  });
}

export default function IpAllowlistPanel({ orgId, namespace, cidrs, yourIp }: IpAllowlistPanelProps) {
  const router = useRouter();
  const [entries, setEntries] = useState<string[]>(cidrs);
  const [newCidr, setNewCidr] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wouldLockOutSelf =
    entries.length > 0 && yourIp !== null && !ipMatchesAnyClient(yourIp, entries);

  async function save(nextEntries: string[]) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/ip-allowlist`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ cidrs: nextEntries }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setEntries(body.cidrs);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  function onAdd(e: React.FormEvent) {
    e.preventDefault();
    const cidr = newCidr.trim();
    if (!cidr || entries.includes(cidr)) return;
    void save([...entries, cidr]);
    setNewCidr("");
  }

  function onRemove(cidr: string) {
    void save(entries.filter((c) => c !== cidr));
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-1 text-base font-medium text-white">Your current request IP</h2>
        <p className="mb-4 text-xs text-gray-500">
          Resolved server-side from <code>x-forwarded-for</code>/<code>x-real-ip</code>, the same
          way middleware.ts resolves the caller IP it enforces against.
        </p>
        <p className="rounded-md border border-border bg-bg px-3 py-2 font-mono text-sm text-white">
          {yourIp ?? "unresolved (no x-forwarded-for/x-real-ip header on this request)"}
        </p>
      </div>

      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">
          Allowed CIDR ranges -- <code>{namespace}</code>
        </h2>
        {entries.length === 0 && (
          <p className="mb-4 text-sm text-gray-500">
            No CIDRs configured -- this org is unrestricted (fail-open default): any IP may reach
            the console.
          </p>
        )}
        {entries.length > 0 && (
          <div className="mb-4 divide-y divide-border">
            {entries.map((cidr) => (
              <div key={cidr} className="flex items-center justify-between gap-4 py-3">
                <span className="font-mono text-sm text-white">{cidr}</span>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onRemove(cidr)}
                  className="rounded-md border border-red-900 bg-red-950/40 px-3 py-1 text-xs text-red-300 hover:bg-red-950/70 disabled:opacity-50"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        )}

        {wouldLockOutSelf && (
          <div className="mb-4 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            Warning: your own request IP (<code>{yourIp}</code>) does not match any CIDR currently
            listed above. Saving further changes without adding a range that covers it will lock
            you out of this console.
          </div>
        )}

        <form onSubmit={onAdd} className="flex items-center gap-2">
          <input
            type="text"
            value={newCidr}
            onChange={(e) => setNewCidr(e.target.value)}
            placeholder="203.0.113.0/24"
            className="flex-1 rounded-md border border-border bg-bg px-3 py-2 font-mono text-sm text-white placeholder:text-gray-600"
          />
          <button
            type="submit"
            disabled={busy || !newCidr.trim()}
            className="rounded-md border border-border bg-panel px-4 py-2 text-sm text-white hover:bg-bg disabled:opacity-50"
          >
            Add
          </button>
        </form>
        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      </div>
    </div>
  );
}
