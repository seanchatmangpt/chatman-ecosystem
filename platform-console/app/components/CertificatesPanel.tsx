"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { ManagedCertificate } from "@/lib/cert-lifecycle";

/**
 * Real Certificate Lifecycle dashboard via /api/certificates ->
 * lib/cert-lifecycle.ts. GET and the rotation POST are both owner-gated
 * server-side (requireRole) -- this panel only ever renders after the
 * server-rendered page has already confirmed the viewer is an owner, but
 * the real enforcement boundary is the route, not this component. No
 * client-side simulation of "rotated" -- a row's serial/notAfter only
 * change after a real 200 (router.refresh() re-reads the live Secrets
 * server-side), same "no optimistic UI" convention CustomDomainsPanel
 * already follows.
 */
export default function CertificatesPanel({
  initialCertificates,
}: {
  initialCertificates: ManagedCertificate[];
}) {
  const router = useRouter();
  const [certificates, setCertificates] = useState(initialCertificates);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onRotate(secretName: string) {
    setBusy(secretName);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch("/api/certificates", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ secretName }),
      });
      const payload = await res.json();
      if (!res.ok) {
        setError(payload.error ?? `HTTP ${res.status}`);
        return;
      }
      const rotation = payload.rotation as {
        secretName: string;
        hostname: string;
        oldSerialNumber: string;
        newSerialNumber: string;
        oldNotAfter: string;
        newNotAfter: string;
      };
      setSuccess(
        `Rotated ${rotation.secretName} (${rotation.hostname}) in place -- ` +
          `serial ${rotation.oldSerialNumber} -> ${rotation.newSerialNumber}, ` +
          `notAfter ${new Date(rotation.oldNotAfter).toISOString()} -> ` +
          `${new Date(rotation.newNotAfter).toISOString()}. Envoy/SDS picks up the new cert on ` +
          "its own watch, no Gateway/VirtualService touched.",
      );
      router.refresh();
      // Also refetch this panel's own list directly so the row updates
      // immediately even before the server component re-renders.
      const refreshed = await fetch("/api/certificates").then((r) => r.json());
      if (Array.isArray(refreshed?.certificates)) {
        setCertificates(refreshed.certificates as ManagedCertificate[]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  const expiringCount = certificates.filter((c) => c.expiringSoon).length;

  return (
    <div className="space-y-6">
      {expiringCount > 0 && (
        <div className="rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
          {expiringCount} certificate{expiringCount === 1 ? "" : "s"} expiring within the
          warning threshold.
        </div>
      )}

      <div className="card overflow-x-auto p-6">
        <h2 className="mb-4 text-base font-medium text-white">Managed certificates</h2>
        {certificates.length === 0 && (
          <p className="text-sm text-gray-500">No TLS-bearing Secrets found in istio-system.</p>
        )}
        {certificates.length > 0 && (
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-border text-xs uppercase tracking-wide text-gray-500">
                <th className="py-2 pr-4">Secret</th>
                <th className="py-2 pr-4">Kind</th>
                <th className="py-2 pr-4">Hostname</th>
                <th className="py-2 pr-4">Serial</th>
                <th className="py-2 pr-4">Expires</th>
                <th className="py-2 pr-4">Days left</th>
                <th className="py-2 pr-4" />
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {certificates.map((c) => (
                <tr key={c.secretName}>
                  <td className="py-2 pr-4">
                    <code className="text-white">{c.secretName}</code>
                  </td>
                  <td className="py-2 pr-4 text-gray-400">{c.kind}</td>
                  <td className="py-2 pr-4 text-gray-400">{c.hostname ?? "—"}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{c.serialNumber}</td>
                  <td className="py-2 pr-4 text-gray-400">
                    {new Date(c.notAfter).toISOString().slice(0, 10)}
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={
                        c.expired
                          ? "text-red-400"
                          : c.expiringSoon
                            ? "text-amber-400"
                            : "text-emerald-400"
                      }
                    >
                      {c.daysUntilExpiry}
                    </span>
                  </td>
                  <td className="py-2 pr-4">
                    {c.rotatable ? (
                      <button
                        type="button"
                        disabled={busy !== null}
                        onClick={() => onRotate(c.secretName)}
                        className="rounded-md border border-accent/60 bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent disabled:opacity-50"
                      >
                        {busy === c.secretName ? "Rotating..." : "Rotate now"}
                      </button>
                    ) : (
                      <span className="text-xs text-gray-600">not rotatable</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {error && (
          <p className="mt-4 break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
            {error}
          </p>
        )}
        {success && (
          <p className="mt-4 break-all rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-300">
            {success}
          </p>
        )}
      </div>
    </div>
  );
}
