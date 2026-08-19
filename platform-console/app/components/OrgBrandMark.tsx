"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

interface OrgBranding {
  productName: string;
  logoUrl: string;
  accentColor: string;
}

const DEFAULT_PRODUCT_NAME = "platform console";
const ACCENT_COLOR_RE = /^#[0-9a-fA-F]{6}$/;

/**
 * Real header brand mark: fetches the current org's branding (GET
 * /api/orgs/[id]/branding, readable by any authenticated member) for the
 * org named by this page's own `?orgId=` query param -- the same
 * query-param scoping app/org/branding/page.tsx uses to pick which org
 * it manages, since this app has no session-wide "current org" concept
 * (see that page's own header comment). No `orgId` in the URL -> renders
 * the default "platform console" wordmark unchanged, exactly as every
 * page did before this capability existed; a set org id whose branding
 * hasn't been configured yet also falls back to the default mark.
 *
 * Sets `--org-accent` as a CSS custom property on `<html>` so any other
 * element on the page (not just this mark) can opt into the org's accent
 * color via `var(--org-accent, <fallback>)` -- cleared back to unset
 * whenever `orgId` changes or its branding has no accentColor, so one
 * org's accent can never bleed into a page rendered for a different org
 * or for no org at all.
 */
export default function OrgBrandMark() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";
  const [branding, setBranding] = useState<OrgBranding | null>(null);

  useEffect(() => {
    if (!orgId) {
      setBranding(null);
      document.documentElement.style.removeProperty("--org-accent");
      return;
    }
    let cancelled = false;
    fetch(`/api/orgs/${encodeURIComponent(orgId)}/branding`)
      .then(async (res) => (res.ok ? ((await res.json()).branding as OrgBranding | null) : null))
      .then((b) => {
        if (cancelled) return;
        setBranding(b);
      })
      .catch(() => {
        if (!cancelled) setBranding(null);
      });
    return () => {
      cancelled = true;
    };
  }, [orgId]);

  useEffect(() => {
    if (branding && ACCENT_COLOR_RE.test(branding.accentColor)) {
      document.documentElement.style.setProperty("--org-accent", branding.accentColor);
    } else {
      document.documentElement.style.removeProperty("--org-accent");
    }
  }, [branding]);

  const productName = branding?.productName || DEFAULT_PRODUCT_NAME;
  const logoUrl = branding?.logoUrl;

  return (
    <span className="inline-flex items-center gap-2">
      {logoUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={logoUrl} alt="" className="h-5 w-5 rounded object-contain" />
      ) : (
        <span
          aria-hidden
          className="inline-flex h-5 w-5 items-center justify-center rounded bg-muted text-[10px] font-bold"
          style={{ color: "var(--org-accent, currentColor)" }}
        >
          PC
        </span>
      )}
      <span style={{ color: "var(--org-accent, inherit)" }}>{productName}</span>
    </span>
  );
}
