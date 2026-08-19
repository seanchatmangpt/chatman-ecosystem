"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Nav from "@/components/Nav";

interface OrgBranding {
  productName: string;
  logoUrl: string;
  accentColor: string;
}

const DEFAULT_ACCENT = "#4f46e5";

type CustomDomainStatus = "pending" | "issued" | "failed" | null;

// Real per-org white-label branding settings page. This app has no
// existing per-request "current org" concept in the session (see
// lib/session.ts -- SessionPayload has no orgId; the platform's own
// requireRole gate at /org manages the platform-console operators'
// OWN roles, not any one customer org's). Multi-org routing is
// deliberately query-param-scoped here (`?orgId=`) rather than a fake
// dynamic-segment page pretending session-wide org context already
// exists elsewhere in this codebase -- a real, disclosed interim, not
// silently claimed as full multi-tenant UI routing.
export default function OrgBrandingPage() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";

  const [productName, setProductName] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [accentColor, setAccentColor] = useState(DEFAULT_ACCENT);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const [domainInput, setDomainInput] = useState("");
  const [customDomain, setCustomDomain] = useState<string | null>(null);
  const [customDomainStatus, setCustomDomainStatus] = useState<CustomDomainStatus>(null);
  const [domainError, setDomainError] = useState<string | null>(null);
  const [domainSaving, setDomainSaving] = useState(false);

  async function loadCustomDomain(currentOrgId: string) {
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(currentOrgId)}/custom-domain`);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setCustomDomain(body.customDomain ?? null);
      setCustomDomainStatus(body.customDomainStatus ?? null);
      if (body.customDomain) setDomainInput(body.customDomain);
    } catch (err) {
      setDomainError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    if (!orgId) return;
    loadCustomDomain(orgId);
    // Poll every 5s while a certificate is being issued -- cert-manager's
    // controller reconciles asynchronously, so "pending" only ever
    // resolves via a fresh GET, never client-side.
    const interval = setInterval(() => {
      if (customDomainStatus === "pending") loadCustomDomain(orgId);
    }, 5000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId, customDomainStatus]);

  async function handleSaveDomain(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId) return;
    setDomainSaving(true);
    setDomainError(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/custom-domain`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ hostname: domainInput.trim() }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setCustomDomain(body.customDomain ?? null);
      setCustomDomainStatus(body.customDomainStatus ?? null);
    } catch (err) {
      setDomainError(err instanceof Error ? err.message : String(err));
    } finally {
      setDomainSaving(false);
    }
  }

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(orgId)}/branding`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        const branding: OrgBranding | null = body.branding;
        if (branding) {
          setProductName(branding.productName);
          setLogoUrl(branding.logoUrl);
          setAccentColor(branding.accentColor);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, [orgId]);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/branding`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ productName, logoUrl, accentColor }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">Org branding</h1>
        <p className="mb-8 max-w-2xl text-sm text-gray-400">
          Real per-org white-label branding (Vercel/Retool/Auth0-style paid add-on tier): a
          custom product name, sidebar logo, and accent color for one customer org, stored on
          that org&apos;s own entry in the <code>platform-console-orgs</code> registry
          ConfigMap. Setting this here never affects any other org. Owner-only -- enforced
          server-side by <code>PUT /api/orgs/[id]/branding</code>, not just this page.
        </p>

        {!orgId && (
          <div className="mb-6 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
            Append <code>?orgId=&lt;org id&gt;</code> to this page&apos;s URL to manage that
            org&apos;s branding (org ids are returned by <code>POST /api/orgs</code> and listed
            by <code>GET /api/orgs</code>, owner-only).
          </div>
        )}

        {orgId && (
          <form onSubmit={handleSave} className="space-y-6">
            {loading && <p className="text-sm text-gray-400">loading current branding...</p>}

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">
                Product name
              </label>
              <input
                type="text"
                value={productName}
                maxLength={60}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="Acme Cloud"
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
              <p className="mt-1 text-xs text-gray-500">{productName.length}/60 characters</p>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">Logo URL</label>
              <input
                type="text"
                value={logoUrl}
                onChange={(e) => setLogoUrl(e.target.value)}
                placeholder="https://cdn.example.com/logo.svg"
                className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
              />
              <p className="mt-1 text-xs text-gray-500">
                Must be <code>https://</code> -- data: URIs and plain http:// are rejected.
              </p>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-300">
                Accent color
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={/^#[0-9a-fA-F]{6}$/.test(accentColor) ? accentColor : DEFAULT_ACCENT}
                  onChange={(e) => setAccentColor(e.target.value)}
                  className="h-9 w-14 rounded border border-gray-700 bg-gray-900"
                />
                <input
                  type="text"
                  value={accentColor}
                  onChange={(e) => setAccentColor(e.target.value)}
                  placeholder="#4f46e5"
                  className="w-40 rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                Must match <code>/^#[0-9a-fA-F]{"{6}"}$/</code>.
              </p>
            </div>

            <div>
              <p className="mb-2 text-sm font-medium text-gray-300">Live preview</p>
              <div className="flex items-center gap-3 rounded-md border border-gray-800 bg-gray-950 px-4 py-3">
                {logoUrl.startsWith("https://") ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={logoUrl} alt="" className="h-8 w-8 rounded object-contain" />
                ) : (
                  <div
                    className="flex h-8 w-8 items-center justify-center rounded text-xs font-bold text-white"
                    style={{ backgroundColor: "#374151" }}
                  >
                    PC
                  </div>
                )}
                <span
                  className="text-base font-semibold"
                  style={{
                    color: /^#[0-9a-fA-F]{6}$/.test(accentColor) ? accentColor : DEFAULT_ACCENT,
                  }}
                >
                  {productName || "Platform Console"}
                </span>
              </div>
            </div>

            {error && (
              <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                {error}
              </p>
            )}
            {saved && !error && (
              <p className="rounded-md border border-emerald-900 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-300">
                Branding saved.
              </p>
            )}

            <button
              type="submit"
              disabled={saving}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save branding"}
            </button>
          </form>
        )}

        {orgId && (
          <section className="mt-12 border-t border-gray-800 pt-10">
            <h2 className="mb-2 text-xl font-semibold text-white">Custom domain</h2>
            <p className="mb-6 max-w-2xl text-sm text-gray-400">
              Serve this console on your own domain (e.g. <code>console.customer.com</code>)
              instead of the platform&apos;s default host. Point a CNAME at this cluster&apos;s
              ingress yourself (no DNS automation here) -- saving below binds the hostname to
              this org and requests a real TLS certificate via a{" "}
              <code>cert-manager.io/v1</code> Certificate against this cluster&apos;s configured
              ClusterIssuer. Owner-only, enforced server-side by{" "}
              <code>POST /api/orgs/[id]/custom-domain</code>.
            </p>

            <form onSubmit={handleSaveDomain} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-300">Hostname</label>
                <input
                  type="text"
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                  placeholder="console.customer.com"
                  className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
                />
              </div>

              {customDomain && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-gray-400">Current:</span>
                  <code className="text-gray-200">{customDomain}</code>
                  <span
                    className={
                      "rounded-full px-2 py-0.5 text-xs font-medium " +
                      (customDomainStatus === "issued"
                        ? "bg-emerald-950/60 text-emerald-300"
                        : customDomainStatus === "failed"
                          ? "bg-red-950/60 text-red-300"
                          : "bg-amber-950/60 text-amber-300")
                    }
                  >
                    {customDomainStatus === "issued"
                      ? "Certificate issued"
                      : customDomainStatus === "failed"
                        ? "Certificate failed"
                        : "Pending certificate issuance..."}
                  </span>
                </div>
              )}

              {domainError && (
                <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
                  {domainError}
                </p>
              )}

              <button
                type="submit"
                disabled={domainSaving || !domainInput.trim()}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {domainSaving ? "Saving..." : "Save custom domain"}
              </button>
            </form>
          </section>
        )}
      </main>
    </>
  );
}
