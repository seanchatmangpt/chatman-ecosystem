"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Nav from "@/components/Nav";

interface SamlConfigState {
  entityId: string;
  ssoUrl: string;
  certificatePem: string;
  status: "unconfigured" | "configured" | "validated";
  updatedAt: string;
}

interface LoadedState {
  samlConfig: SamlConfigState | null;
  assertionConsumptionWired: boolean;
}

// Real, config-only SAML 2.0 metadata settings page -- backs
// lib/saml-config.ts and app/api/orgs/[id]/saml-config/route.ts. Owner-
// only writes (same requireRoleIn("owner") floor as /branding, /region).
//
// This page is deliberately NOT a working SSO setup flow: the banner
// below states, every time this page renders (not just on first visit),
// that SAML assertion consumption is not yet wired -- so this surface
// can never be mistaken for functioning single sign-on. Login continues
// through the existing OIDC/Supabase path (lib/oidc-federation.ts,
// lib/session.ts) regardless of what is saved here.
export default function SsoSettingsPage() {
  const params = useParams<{ id: string }>();
  const orgId = params?.id ?? "";

  const [state, setState] = useState<LoadedState | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [entityId, setEntityId] = useState("");
  const [ssoUrl, setSsoUrl] = useState("");
  const [certificatePem, setCertificatePem] = useState("");

  function load() {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    fetch(`/api/orgs/${encodeURIComponent(orgId)}/saml-config`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
        setState(body as LoadedState);
        if (body.samlConfig) {
          const c = body.samlConfig as SamlConfigState;
          setEntityId(c.entityId);
          setSsoUrl(c.ssoUrl);
          setCertificatePem(c.certificatePem);
        }
      })
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(load, [orgId]);

  async function handleSave(event: React.FormEvent) {
    event.preventDefault();
    if (!orgId) return;
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      const res = await fetch(`/api/orgs/${encodeURIComponent(orgId)}/saml-config`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ entityId, ssoUrl, certificatePem }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `request failed (${res.status})`);
      setNotice("SAML metadata saved and validated as well-formed.");
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="mx-auto max-w-4xl px-6 py-10">
        <h1 className="mb-2 text-2xl font-semibold text-white">SAML 2.0 single sign-on</h1>
        <p className="mb-6 max-w-2xl text-sm text-gray-400">
          Configure this org&apos;s identity provider metadata for SAML 2.0 (ADFS, Okta, Azure AD,
          or any SAML-compliant IdP). Metadata is validated as structurally well-formed on save --
          entity ID as a URI, SSO URL as https, and the signing certificate as a real, parseable
          X.509 certificate -- with no network call made to your IdP.
        </p>

        <div className="mb-8 rounded-md border border-amber-900 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
          <strong>Not yet wired for login.</strong> This page only validates and stores your IdP&apos;s
          metadata ahead of time. SAML assertion consumption is not implemented -- signing in to
          this org still goes through the existing OIDC/Supabase login path. No session can be
          authenticated from what you save here until a later release adds the real
          assertion-consumer-service endpoint.
        </div>

        {loading && <p className="text-sm text-gray-400">loading...</p>}

        {state?.samlConfig && (
          <div className="mb-6 rounded-md border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-300">
            Status:{" "}
            <span className="rounded-full bg-indigo-950/60 px-2 py-0.5 text-xs text-indigo-300">
              {state.samlConfig.status}
            </span>{" "}
            -- last saved {new Date(state.samlConfig.updatedAt).toLocaleString()}
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-5">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">Entity ID</label>
            <input
              value={entityId}
              onChange={(e) => setEntityId(e.target.value)}
              placeholder="https://idp.example.com/saml/metadata or urn:example:idp"
              className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">SSO URL</label>
            <input
              value={ssoUrl}
              onChange={(e) => setSsoUrl(e.target.value)}
              placeholder="https://idp.example.com/saml/sso"
              className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-white"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300">
              Signing certificate (PEM)
            </label>
            <textarea
              value={certificatePem}
              onChange={(e) => setCertificatePem(e.target.value)}
              placeholder="-----BEGIN CERTIFICATE-----&#10;...&#10;-----END CERTIFICATE-----"
              rows={8}
              className="w-full rounded-md border border-gray-700 bg-gray-900 px-3 py-2 font-mono text-xs text-white"
            />
          </div>

          {error && (
            <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-2 text-sm text-red-300">
              {error}
            </p>
          )}
          {notice && !error && (
            <p className="rounded-md border border-emerald-900 bg-emerald-950/40 px-4 py-2 text-sm text-emerald-300">
              {notice}
            </p>
          )}

          <button
            type="submit"
            disabled={saving || !orgId}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save SAML metadata"}
          </button>
        </form>
      </main>
    </>
  );
}
