"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

// Landing page for an admin-issued invite link (`/org/invite?token=...`,
// minted by POST /api/org-invites). This page itself does no
// verification -- the token's signature/expiry is only ever checked
// server-side by POST /api/orgs, never trusted client-side -- it exists
// purely to hand the token to /signup under the `invite` query param the
// signup form already reads.
function InviteRedirect() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  useEffect(() => {
    if (token) {
      router.replace(`/signup?invite=${encodeURIComponent(token)}`);
    }
  }, [token, router]);

  if (!token) {
    return (
      <p className="rounded-md border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300">
        missing invite token
      </p>
    );
  }
  return <p className="text-sm text-gray-400">Redirecting to signup...</p>;
}

export default function OrgInvitePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-bg px-4">
      <Suspense fallback={null}>
        <InviteRedirect />
      </Suspense>
    </main>
  );
}
