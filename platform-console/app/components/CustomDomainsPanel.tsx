"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import type { K8sService } from "@/lib/k8s";
import type { CustomDomainBinding } from "@/lib/custom-domains";

/**
 * Registers/lists/unbinds real Custom Domain bindings via
 * /api/custom-domains -> lib/custom-domains.ts. Both GET and every
 * mutation on that route are owner-gated server-side (requireRole) -- this
 * panel only ever renders after the server-rendered page has already
 * confirmed the viewer is an owner, but the real enforcement boundary is
 * the route, not this component. No client-side simulation of "bound" --
 * the bindings list only changes after a real 200/201/DELETE
 * (router.refresh() re-reads the live Gateway objects server-side), same
 * "no optimistic UI" convention CanaryPanel/OrgRolesPanel already follow.
 */
export default function CustomDomainsPanel({
  services,
  initialBindings,
}: {
  services: K8sService[];
  initialBindings: CustomDomainBinding[];
}) {
  const router = useRouter();
  const [bindings, setBindings] = useState(initialBindings);
  const [hostname, setHostname] = useState("");
  const [selectedKey, setSelectedKey] = useState(
    services.length > 0 ? `${services[0].namespace}/${services[0].name}` : "",
  );
  const [selectedPort, setSelectedPort] = useState<number | "">(
    services[0]?.ports[0]?.port ?? "",
  );
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const selectedService = useMemo(
    () => services.find((s) => `${s.namespace}/${s.name}` === selectedKey) ?? null,
    [services, selectedKey],
  );

  function onSelectService(key: string) {
    setSelectedKey(key);
    const svc = services.find((s) => `${s.namespace}/${s.name}` === key);
    setSelectedPort(svc?.ports[0]?.port ?? "");
  }

  async function onRegister(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedService || selectedPort === "") return;
    setBusy("register");
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch("/api/custom-domains", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          hostname,
          serviceName: selectedService.name,
          serviceNamespace: selectedService.namespace,
          servicePort: selectedPort,
        }),
      });
      const payload = await res.json();
      if (!res.ok) {
        setError(payload.error ?? `HTTP ${res.status}`);
        return;
      }
      const binding = payload.binding as CustomDomainBinding;
      setBindings((prev) => [...prev.filter((b) => b.hostname !== binding.hostname), binding]);
      setSuccess(
        `Registered ${binding.hostname} -> ${binding.target.serviceName}.${binding.target.serviceNamespace}:${binding.target.servicePort} ` +
          `(Secret/${binding.secretName}, Gateway/${binding.gatewayName}, VirtualService/${binding.virtualServiceName} in istio-system/platform-console)`,
      );
      setHostname("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  async function onUnbind(hostnameToUnbind: string) {
    setBusy(`unbind:${hostnameToUnbind}`);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(`/api/custom-domains?hostname=${encodeURIComponent(hostnameToUnbind)}`, {
        method: "DELETE",
      });
      const payload = await res.json();
      if (!res.ok) {
        setError(payload.error ?? `HTTP ${res.status}`);
        return;
      }
      setBindings((prev) => prev.filter((b) => b.hostname !== hostnameToUnbind));
      setSuccess(`Unbound ${hostnameToUnbind} -- Gateway/VirtualService/Secret deleted.`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Active bindings</h2>
        {bindings.length === 0 && (
          <p className="text-sm text-gray-500">No custom domains registered yet.</p>
        )}
        {bindings.length > 0 && (
          <div className="divide-y divide-border">
            {bindings.map((b) => (
              <div key={b.hostname} className="flex items-center justify-between gap-4 py-3">
                <div>
                  <p className="text-sm font-medium text-white">
                    <code>{b.hostname}</code>
                    <span className="ml-2 text-xs text-gray-500">:8443</span>
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    -&gt; <code>{b.target.serviceName}.{b.target.serviceNamespace}</code>:
                    {b.target.servicePort} -- Secret/<code>{b.secretName}</code> (istio-system),
                    Gateway/<code>{b.gatewayName}</code>, VirtualService/
                    <code>{b.virtualServiceName}</code> (platform-console)
                  </p>
                </div>
                <button
                  type="button"
                  disabled={busy !== null}
                  onClick={() => onUnbind(b.hostname)}
                  className="rounded-md border border-red-800 bg-red-950/40 px-3 py-1.5 text-xs font-medium text-red-300 disabled:opacity-50"
                >
                  {busy === `unbind:${b.hostname}` ? "Unbinding..." : "Unbind"}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <form onSubmit={onRegister} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Register a new domain</h2>
        <p className="text-xs text-gray-500">
          Generates a real, freshly-issued TLS certificate for the hostname you enter (SAN
          re-verified before storage) and binds it, over a real Istio Gateway on port{" "}
          <code>8443</code>, to whichever Service you pick below -- the same live Service list
          Service Discovery reads.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Hostname</span>
            <input
              required
              pattern="[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)+"
              title="a dotted DNS hostname, e.g. demo.platform.local"
              value={hostname}
              onChange={(e) => setHostname(e.target.value.trim().toLowerCase())}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder="demo.platform.local"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Target service</span>
            <select
              required
              value={selectedKey}
              onChange={(e) => onSelectService(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            >
              {services.map((s) => (
                <option key={`${s.namespace}/${s.name}`} value={`${s.namespace}/${s.name}`}>
                  {s.name}.{s.namespace}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Target port</span>
          <select
            required
            value={selectedPort}
            onChange={(e) => setSelectedPort(Number(e.target.value))}
            className="w-full max-w-[12rem] rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          >
            {(selectedService?.ports ?? []).map((p) => (
              <option key={p.port} value={p.port}>
                {p.port}
                {p.name ? ` (${p.name})` : ""}
              </option>
            ))}
          </select>
        </label>

        <button
          type="submit"
          disabled={busy !== null || !selectedService || selectedPort === ""}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy === "register" ? "Registering..." : "Register domain"}
        </button>
        {error && (
          <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
            {error}
          </p>
        )}
        {success && (
          <p className="break-all rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-300">
            {success}
          </p>
        )}
      </form>
    </div>
  );
}
