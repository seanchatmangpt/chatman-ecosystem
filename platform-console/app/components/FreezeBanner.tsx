"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

interface ActiveFreezeWindow {
  id: string;
  reason: string;
  endsAt: string;
  allowEmergencyOverride: boolean;
}

// Real, site-wide "a change freeze is active right now" banner
// (lib/freeze-windows.ts) -- rendered inside components/Nav.tsx so every
// console page (not just app/org/freeze-windows) surfaces it. Same
// query-param-scoped `?orgId=` interim every other org-settings page in
// this app already uses -- when no `orgId` is present (most non-org
// pages, or the very first load before a user has navigated from an
// org-scoped link), this renders nothing; it never guesses an org. A
// GET request only (`viewer` role, same as the freeze-windows page
// itself) -- this banner never mutates anything and is safe to render
// unconditionally for any authenticated member of the org.
export default function FreezeBanner() {
  const searchParams = useSearchParams();
  const orgId = searchParams.get("orgId") ?? "";
  const [active, setActive] = useState<ActiveFreezeWindow[]>([]);

  useEffect(() => {
    if (!orgId) {
      setActive([]);
      return;
    }
    let cancelled = false;
    fetch(`/api/freeze-windows?orgId=${encodeURIComponent(orgId)}`)
      .then(async (res) => {
        if (!res.ok) return;
        const body = await res.json();
        const windows = (body.windows ?? []) as Array<{
          id: string;
          reason: string;
          startsAt: string;
          endsAt: string;
          allowEmergencyOverride: boolean;
        }>;
        const now = Date.now();
        const nowActive = windows.filter(
          (w) => Date.parse(w.startsAt) <= now && now <= Date.parse(w.endsAt),
        );
        if (!cancelled) setActive(nowActive);
      })
      .catch(() => {
        // Fails silently -- this is an informational banner, not the
        // real enforcement point (checkFreezeGuard on the server is).
        // A failed fetch here must never itself claim "no freeze active".
      });
    return () => {
      cancelled = true;
    };
  }, [orgId]);

  if (active.length === 0) return null;

  return (
    <div className="w-full border-b border-red-900 bg-red-950/70 px-6 py-2 text-center text-sm text-red-200">
      {active.length === 1 ? (
        <>
          Change freeze active: <strong>{active[0].reason}</strong> -- ends{" "}
          {new Date(active[0].endsAt).toLocaleString()}.
        </>
      ) : (
        <>{active.length} change freeze windows are active for this org right now.</>
      )}{" "}
      Deployments, tier changes, and quota patches are blocked.{" "}
      <Link
        href={`/org/freeze-windows?orgId=${encodeURIComponent(orgId)}`}
        className="underline hover:text-white"
      >
        View freeze windows
      </Link>
    </div>
  );
}
