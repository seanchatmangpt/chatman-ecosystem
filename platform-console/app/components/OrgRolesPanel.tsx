"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { OrgRoleAssignment, Role } from "@/lib/authz";

const ROLE_OPTIONS: Role[] = ["viewer", "member", "owner"];

/**
 * Reads/writes the real platform-console-org-roles ConfigMap via
 * /api/org/roles -> lib/authz.ts's getOrgRoleAssignments/setOrgRole. Both
 * GET and POST on that route are owner-gated server-side (requireRole) --
 * this panel only ever renders after the server-rendered org page has
 * already confirmed the viewer is an owner, but the real enforcement
 * boundary is the route, not this component. No client-side simulation
 * of "role changed" -- a row's displayed role only changes after a real
 * 200 (router.refresh() re-reads the live ConfigMap server-side), same
 * "no optimistic UI" convention every other mutating panel in this
 * console follows (FeatureFlagsPanel, CreateSecretForm).
 */
export default function OrgRolesPanel({
  assignments,
  currentIdentifier,
}: {
  assignments: OrgRoleAssignment[];
  currentIdentifier: string;
}) {
  const router = useRouter();
  const [busyIdentifier, setBusyIdentifier] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newIdentifier, setNewIdentifier] = useState("");
  const [newRole, setNewRole] = useState<Role>("viewer");
  const [creating, setCreating] = useState(false);

  async function setRole(identifier: string, role: Role) {
    setBusyIdentifier(identifier);
    setError(null);
    try {
      const res = await fetch("/api/org/roles", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ identifier, role }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? body.reason ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyIdentifier(null);
    }
  }

  async function onAssign(e: React.FormEvent) {
    e.preventDefault();
    const identifier = newIdentifier.trim();
    if (!identifier) return;
    setCreating(true);
    await setRole(identifier, newRole);
    setCreating(false);
    setNewIdentifier("");
    setNewRole("viewer");
  }

  const sorted = [...assignments].sort((a, b) => a.identifier.localeCompare(b.identifier));

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Role assignments</h2>
        {sorted.length === 0 && (
          <p className="text-sm text-gray-500">
            No role assignments yet -- the <code>platform-console-org-roles</code> ConfigMap does
            not exist or is empty.
          </p>
        )}
        {sorted.length > 0 && (
          <div className="divide-y divide-border">
            {sorted.map(({ identifier, role }) => (
              <div key={identifier} className="flex items-center justify-between gap-4 py-3">
                <div>
                  <p className="text-sm font-medium text-white">
                    {identifier}
                    {identifier === currentIdentifier && (
                      <span className="ml-2 text-xs text-gray-500">(you)</span>
                    )}
                  </p>
                  <p className="text-xs text-gray-500">
                    role: <code>{role}</code>
                  </p>
                </div>
                <select
                  value={role}
                  disabled={busyIdentifier === identifier}
                  onChange={(e) => setRole(identifier, e.target.value as Role)}
                  className="rounded-md border border-border bg-bg px-3 py-1.5 text-xs text-white disabled:opacity-50"
                >
                  {ROLE_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={onAssign} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Assign / change a role</h2>
        <p className="text-xs text-gray-500">
          Submits a real ConfigMap merge patch via the console&apos;s ServiceAccount. Identifier
          is a gotrue user&apos;s email, or <code>admin</code> for the local-admin account.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Identifier (email or &quot;admin&quot;)</span>
            <input
              required
              value={newIdentifier}
              onChange={(e) => setNewIdentifier(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder="user@example.com"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Role</span>
            <select
              value={newRole}
              onChange={(e) => setNewRole(e.target.value as Role)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              {ROLE_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
        </div>
        <button
          type="submit"
          disabled={creating}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {creating ? "Saving..." : "Save role"}
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
