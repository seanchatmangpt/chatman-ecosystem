"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { ApiKeySummary } from "@/lib/api-keys";
import {
  API_KEY_MODES,
  API_KEY_TIERS,
  SANDBOX_TIER_LIMIT,
  TIER_LIMITS,
  type ApiKeyMode,
  type ApiKeyTier,
} from "@/lib/rate-limit";

const ROLE_OPTIONS = ["viewer", "member", "owner"] as const;

/**
 * Creates/lists/revokes real API keys via /api/api-keys -> lib/api-keys.ts.
 * The plaintext key returned by a successful create is held ONLY in this
 * component's local state, shown exactly once, and never re-fetchable --
 * navigating away or refreshing loses it permanently, matching every real
 * provider's (AWS/GCP/Stripe) own "shown once" UX. No client-side
 * simulation of "created"/"revoked": a row only appears/updates after a
 * real 201/200 from the API route (router.refresh() re-reads the live
 * Secret server-side), same "no optimistic UI" convention every other
 * mutating panel in this console follows.
 */
export default function ApiKeysPanel({
  keys,
  creatorRole,
  orgs,
}: {
  keys: ApiKeySummary[];
  creatorRole: string;
  // Orgs this identity may mint a key for (owner-role, per requireRoleIn
  // on /api/orgs/[id]/api-keys). A key's `orgId` is formal, required
  // ownership (lib/api-keys.ts) -- creation requires picking one, never
  // defaults silently. "unassigned" is not offered as a creatable option;
  // it only ever appears on pre-existing keys the backfill script
  // (scripts/backfill-api-key-org.ts) could not confidently resolve.
  orgs: { id: string; name: string }[];
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [role, setRole] = useState<string>(creatorRole);
  const [tier, setTier] = useState<ApiKeyTier>("standard");
  const [mode, setMode] = useState<ApiKeyMode>("live");
  const [orgId, setOrgId] = useState<string>(orgs[0]?.id ?? "");
  const [orgFilter, setOrgFilter] = useState<string>("all");
  const [creating, setCreating] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [justCreated, setJustCreated] = useState<{ plaintext: string; prefix: string } | null>(
    null,
  );
  // Per-key pending selection for the rate-limit tier upgrade/downgrade
  // control -- keyed by key id so each row's <select> is independent.
  const [pendingTier, setPendingTier] = useState<Record<string, ApiKeyTier>>({});
  const [upgradingId, setUpgradingId] = useState<string | null>(null);

  async function onUpgrade(id: string, currentTier: ApiKeyTier) {
    const nextTier = pendingTier[id] ?? currentTier;
    if (nextTier === currentTier) return;
    const tenantNamespace =
      nextTier === "pro" || nextTier === "enterprise"
        ? window.prompt(
            `Upgrading to '${nextTier}' attaches a real Stripe rate-limit add-on price to your org's subscription. Which tenant namespace's subscription should be billed?`,
            "platform-console",
          )
        : null;
    if ((nextTier === "pro" || nextTier === "enterprise") && !tenantNamespace) return;

    setUpgradingId(id);
    setError(null);
    try {
      const res = await fetch(`/api/api-keys/${encodeURIComponent(id)}/rate-limit`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ tier: nextTier, tenantNamespace: tenantNamespace ?? undefined }),
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
      setUpgradingId(null);
    }
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!orgId) {
      setError("an org must be selected to create a key");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/api-keys`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, role, tier, mode }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? body.reason ?? `HTTP ${res.status}`);
        return;
      }
      setJustCreated({ plaintext: body.plaintext, prefix: body.key.prefix });
      setName("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  }

  async function onRevoke(id: string) {
    if (!confirm("Revoke this API key? Any client using it will start getting a real 401 immediately.")) {
      return;
    }
    setRevokingId(id);
    setError(null);
    try {
      const res = await fetch(`/api/api-keys?id=${encodeURIComponent(id)}`, {
        method: "DELETE",
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
      setRevokingId(null);
    }
  }

  const orgNameById = new Map(orgs.map((o) => [o.id, o.name]));
  const sorted = [...keys]
    .filter((k) => orgFilter === "all" || k.orgId === orgFilter)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));

  return (
    <div className="space-y-6">
      {justCreated && (
        <div className="card space-y-2 border-emerald-900 bg-emerald-950/30 p-6">
          <p className="text-sm font-medium text-emerald-300">
            Key created -- this is the only time the full value is ever shown.
          </p>
          <code className="block break-all rounded-md border border-border bg-bg px-3 py-2 text-xs text-white">
            {justCreated.plaintext}
          </code>
          <p className="text-xs text-gray-500">
            Copy it now. After this, the console only ever shows the prefix (
            <code>{justCreated.prefix}</code>) -- the plaintext is not recoverable.
          </p>
          <button
            type="button"
            onClick={() => setJustCreated(null)}
            className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-300 hover:text-white"
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="card p-6">
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-base font-medium text-white">Keys</h2>
          <label className="flex items-center gap-2 text-xs text-gray-400">
            Org
            <select
              value={orgFilter}
              onChange={(e) => setOrgFilter(e.target.value)}
              className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs text-white"
            >
              <option value="all">all orgs</option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
              <option value="unassigned">unassigned (needs reassignment)</option>
            </select>
          </label>
        </div>
        {sorted.length === 0 && (
          <p className="text-sm text-gray-500">No API keys yet -- create one below.</p>
        )}
        {sorted.length > 0 && (
          <div className="divide-y divide-border">
            {sorted.map((k) => (
              <div key={k.id} className="flex items-center justify-between gap-4 py-3">
                <div>
                  <p className="text-sm font-medium text-white">
                    <code>{k.prefix}</code>
                    {k.mode === "sandbox" ? (
                      <span
                        className="ml-2 rounded-md border border-amber-800 bg-amber-950/40 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-300"
                        title={`Sandbox key -- fixed ${SANDBOX_TIER_LIMIT.maxTokens} req/${SANDBOX_TIER_LIMIT.fillIntervalMs / 1000}s ceiling, zero billing/overage impact, no real k8s resources.`}
                      >
                        sandbox
                      </span>
                    ) : (
                      <span className="ml-2 rounded-md border border-emerald-900 bg-emerald-950/30 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-400">
                        live
                      </span>
                    )}
                    {k.name && <span className="ml-2 text-gray-400">{k.name}</span>}
                  </p>
                  <p className="text-xs text-gray-500">
                    org:{" "}
                    <code className={k.orgId === "unassigned" ? "text-amber-400" : undefined}>
                      {orgNameById.get(k.orgId) ?? k.orgId}
                    </code>
                    {k.orgId === "unassigned" && (
                      <span className="ml-1 text-amber-400">(needs reassignment)</span>
                    )}{" "}
                    · identifier: <code>{k.identifier}</code> · role: <code>{k.role}</code> · tier:{" "}
                    <code>{k.tier}</code> ({TIER_LIMITS[k.tier].maxTokens} req/
                    {TIER_LIMITS[k.tier].fillIntervalMs / 1000}s) · created by{" "}
                    <code>{k.createdBy}</code> at{" "}
                    {new Date(k.createdAt).toLocaleString()}
                    {k.revoked && (
                      <>
                        {" "}
                        ·{" "}
                        <span className="text-red-400">
                          revoked at {k.revokedAt ? new Date(k.revokedAt).toLocaleString() : ""}
                        </span>
                      </>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {!k.revoked && (
                    <>
                      <select
                        value={pendingTier[k.id] ?? k.tier}
                        onChange={(e) =>
                          setPendingTier((prev) => ({
                            ...prev,
                            [k.id]: e.target.value as ApiKeyTier,
                          }))
                        }
                        className="rounded-md border border-border bg-bg px-2 py-1.5 text-xs text-white"
                      >
                        {API_KEY_TIERS.map((t) => (
                          <option key={t} value={t}>
                            {t} ({TIER_LIMITS[t].maxTokens} req/{TIER_LIMITS[t].fillIntervalMs / 1000}s)
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => onUpgrade(k.id, k.tier)}
                        disabled={
                          upgradingId === k.id || (pendingTier[k.id] ?? k.tier) === k.tier
                        }
                        className="rounded-md border border-accent px-3 py-1.5 text-xs text-accent hover:bg-accent/10 disabled:opacity-50"
                      >
                        {upgradingId === k.id ? "Updating..." : "Update tier"}
                      </button>
                    </>
                  )}
                  {!k.revoked ? (
                    <button
                      type="button"
                      onClick={() => onRevoke(k.id)}
                      disabled={revokingId === k.id}
                      className="rounded-md border border-red-900 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
                    >
                      {revokingId === k.id ? "Revoking..." : "Revoke"}
                    </button>
                  ) : (
                    <span className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-500">
                      revoked
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={onCreate} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Create a key</h2>
        <p className="text-xs text-gray-500">
          Bound to your own identity. Role can be at most your own current role (
          <code>{creatorRole}</code>) -- never escalated, regardless of what is selected here.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Org (required)</span>
            <select
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              required
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              <option value="" disabled>
                select an org...
              </option>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Name (optional)</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder="ci-pipeline"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Role</span>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              {ROLE_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Plan tier (rate limit)</span>
            <select
              value={tier}
              onChange={(e) => setTier(e.target.value as ApiKeyTier)}
              disabled={mode === "sandbox"}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white disabled:opacity-50"
            >
              {API_KEY_TIERS.map((t) => (
                <option key={t} value={t}>
                  {t} ({TIER_LIMITS[t].maxTokens} req/{TIER_LIMITS[t].fillIntervalMs / 1000}s)
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Key class</span>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as ApiKeyMode)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              {API_KEY_MODES.map((m) => (
                <option key={m} value={m}>
                  {m === "sandbox"
                    ? `sandbox (fixed ${SANDBOX_TIER_LIMIT.maxTokens} req/${SANDBOX_TIER_LIMIT.fillIntervalMs / 1000}s, zero billing impact)`
                    : "live (real quota + billing)"}
                </option>
              ))}
            </select>
          </label>
        </div>
        {mode === "sandbox" && (
          <p className="text-xs text-amber-400">
            Sandbox keys are for CI/integration testing only -- they carry a fixed{" "}
            {SANDBOX_TIER_LIMIT.maxTokens} req/{SANDBOX_TIER_LIMIT.fillIntervalMs / 1000}s ceiling
            regardless of plan tier, and requests made with them are excluded entirely from usage
            metering and overage billing.
          </p>
        )}
        <button
          type="submit"
          disabled={creating || !orgId}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {creating ? "Creating..." : "Create key"}
        </button>
      </form>

      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}
