"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { CustomRole, CustomRoleGrant, Permission } from "@/lib/custom-roles";

/**
 * Reads/writes the real platform-console-custom-roles ConfigMap via
 * /api/roles -> lib/custom-roles.ts. Owner-gated server-side on that
 * route (requireRole) -- this panel only ever renders after the
 * server-rendered /org/roles page has already confirmed the viewer is an
 * owner, but the real enforcement boundary is the route, not this
 * component. No optimistic UI: a change is only reflected after a real
 * 200 (router.refresh() re-reads the live ConfigMap server-side), same
 * convention as OrgRolesPanel.
 */
export default function CustomRolesPanel({
  roles,
  grants,
  permissions,
  currentIdentifier,
}: {
  roles: CustomRole[];
  grants: CustomRoleGrant[];
  permissions: readonly Permission[];
  currentIdentifier: string;
}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [newName, setNewName] = useState("");
  const [newPermissions, setNewPermissions] = useState<Permission[]>([]);

  const [grantIdentifier, setGrantIdentifier] = useState("");
  const [grantRoleId, setGrantRoleId] = useState("");

  async function post(body: Record<string, unknown>) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/roles", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body),
      });
      const responseBody = await res.json();
      if (!res.ok) {
        setError(responseBody.error ?? responseBody.reason ?? `HTTP ${res.status}`);
        return false;
      }
      router.refresh();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return false;
    } finally {
      setBusy(false);
    }
  }

  async function onCreateRole(e: React.FormEvent) {
    e.preventDefault();
    const name = newName.trim();
    if (!name || newPermissions.length === 0) return;
    const ok = await post({ action: "upsert-role", name, permissions: newPermissions });
    if (ok) {
      setNewName("");
      setNewPermissions([]);
    }
  }

  async function onDeleteRole(id: string) {
    await post({ action: "delete-role", id });
  }

  async function onAssign(e: React.FormEvent) {
    e.preventDefault();
    const identifier = grantIdentifier.trim();
    if (!identifier || !grantRoleId) return;
    const existing = grants.find((g) => g.identifier === identifier)?.roleIds ?? [];
    const roleIds = Array.from(new Set([...existing, grantRoleId]));
    const ok = await post({ action: "set-grants", identifier, roleIds });
    if (ok) {
      setGrantIdentifier("");
      setGrantRoleId("");
    }
  }

  async function onUnassign(identifier: string, roleId: string) {
    const existing = grants.find((g) => g.identifier === identifier)?.roleIds ?? [];
    const roleIds = existing.filter((id) => id !== roleId);
    await post({ action: "set-grants", identifier, roleIds });
  }

  function togglePermission(p: Permission) {
    setNewPermissions((prev) => (prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]));
  }

  return (
    <div className="space-y-6">
      {error && (
        <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Custom roles</h2>
        {roles.length === 0 && (
          <p className="text-sm text-gray-500">
            No custom roles defined yet. Define one below (e.g. &quot;billing-only admin&quot;,
            &quot;read-only auditor with DSAR export rights&quot;).
          </p>
        )}
        {roles.length > 0 && (
          <div className="divide-y divide-border">
            {roles.map((role) => (
              <div key={role.id} className="flex items-center justify-between gap-4 py-3">
                <div>
                  <p className="text-sm font-medium text-white">{role.name}</p>
                  <p className="text-xs text-gray-500">
                    {role.permissions.length > 0 ? (
                      role.permissions.map((p) => (
                        <code key={p} className="mr-1.5">
                          {p}
                        </code>
                      ))
                    ) : (
                      <span className="italic">no permissions</span>
                    )}
                  </p>
                </div>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onDeleteRole(role.id)}
                  className="rounded-md border border-red-900 px-3 py-1.5 text-xs text-red-300 hover:bg-red-950/40 disabled:opacity-50"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={onCreateRole} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Define a custom role</h2>
        <p className="text-xs text-gray-500">
          A named subset of fine-grained permissions -- least-privilege access narrower than the
          built-in <code>viewer</code>/<code>member</code>/<code>owner</code> ladder.
        </p>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Name</span>
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="billing-only admin"
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          />
        </label>
        <div>
          <span className="mb-2 block text-sm text-gray-400">Permissions</span>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {permissions.map((p) => (
              <label key={p} className="flex items-center gap-2 text-xs text-gray-300">
                <input
                  type="checkbox"
                  checked={newPermissions.includes(p)}
                  onChange={() => togglePermission(p)}
                />
                <code>{p}</code>
              </label>
            ))}
          </div>
        </div>
        <button
          type="submit"
          disabled={busy || !newName.trim() || newPermissions.length === 0}
          className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
        >
          Create role
        </button>
      </form>

      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Identifier assignments</h2>
        {grants.length === 0 && (
          <p className="text-sm text-gray-500">No identifiers have a custom role assigned yet.</p>
        )}
        {grants.length > 0 && (
          <div className="divide-y divide-border">
            {grants.map(({ identifier, roleIds }) => (
              <div key={identifier} className="py-3">
                <p className="text-sm font-medium text-white">
                  {identifier}
                  {identifier === currentIdentifier && (
                    <span className="ml-2 text-xs text-gray-500">(you)</span>
                  )}
                </p>
                <div className="mt-1 flex flex-wrap gap-2">
                  {roleIds.map((roleId) => {
                    const role = roles.find((r) => r.id === roleId);
                    return (
                      <span
                        key={roleId}
                        className="flex items-center gap-1 rounded-full border border-border px-2 py-0.5 text-xs text-gray-300"
                      >
                        {role?.name ?? roleId}
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => onUnassign(identifier, roleId)}
                          className="text-gray-500 hover:text-red-300 disabled:opacity-50"
                          aria-label={`remove ${role?.name ?? roleId} from ${identifier}`}
                        >
                          ×
                        </button>
                      </span>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={onAssign} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Assign a custom role</h2>
        <p className="text-xs text-gray-500">
          Identifier is a gotrue user&apos;s email, or <code>admin</code> for the local-admin
          account -- same identifier space the built-in role assignments use.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Identifier</span>
            <input
              type="text"
              value={grantIdentifier}
              onChange={(e) => setGrantIdentifier(e.target.value)}
              placeholder="user@example.com"
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Role</span>
            <select
              value={grantRoleId}
              onChange={(e) => setGrantRoleId(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              <option value="">Select a role</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <button
          type="submit"
          disabled={busy || !grantIdentifier.trim() || !grantRoleId}
          className="rounded-md bg-white px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
        >
          Assign
        </button>
      </form>
    </div>
  );
}
