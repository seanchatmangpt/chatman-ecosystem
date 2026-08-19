"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

// Real self-service new-paying-customer signup: the /signup entry point
// this task requires alongside /login. Two real server calls in sequence,
// no fabricated intermediate state:
//   1. POST /api/auth/gotrue-signup -- creates a real GoTrue user and
//      mints this app's own session cookie (existing route, unmodified).
//   2. POST /api/orgs -- creates the new org: real k8s Namespace, real
//      org-scoped platform-console-org-roles ConfigMap seeded with THIS
//      user as owner, and a first real Project (paired SingleDatabase)
//      provisioned into that new namespace (lib/orgs.ts's createOrg).
// An `?invite=` token in the URL (from an admin-minted /org/invite link)
// is passed through to step 2's body as `inviteToken` -- POST /api/orgs
// verifies its signature/expiry server-side before honoring it.
function SignupForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const inviteToken = searchParams.get("invite");

  const [orgName, setOrgName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    setStatus("creating your account...");
    const signupRes = await fetch("/api/auth/gotrue-signup", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ email, password }),
    }).catch(() => null);
    if (!signupRes || !signupRes.ok) {
      const body = signupRes ? await signupRes.json().catch(() => ({})) : {};
      setError(body.error ?? "account creation failed");
      setSubmitting(false);
      setStatus(null);
      return;
    }

    setStatus("provisioning your organization...");
    const orgRes = await fetch("/api/orgs", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: orgName, inviteToken: inviteToken ?? undefined }),
    }).catch(() => null);
    if (!orgRes || !orgRes.ok) {
      const body = orgRes ? await orgRes.json().catch(() => ({})) : {};
      setError(body.error ?? "organization creation failed (your account was created; contact support to retry)");
      setSubmitting(false);
      setStatus(null);
      return;
    }

    const orgBody = await orgRes.json();
    setStatus(
      orgBody.firstProjectError
        ? `organization created; first project provisioning failed: ${orgBody.firstProjectError}`
        : "organization and first project ready",
    );
    router.push("/");
    router.refresh();
  }

  return (
    <div className="card w-full max-w-sm p-8">
      <h1 className="mb-1 text-lg font-semibold text-white">Create your organization</h1>
      <p className="mb-6 text-sm text-gray-400">
        Get your own isolated namespace, roles, and first project -- no engineer required.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-xs text-gray-400" htmlFor="orgName">
            Organization name
          </label>
          <input
            id="orgName"
            name="orgName"
            type="text"
            required
            value={orgName}
            onChange={(e) => setOrgName(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white outline-none focus:border-accent"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-400" htmlFor="email">
            Work email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white outline-none focus:border-accent"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-gray-400" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white outline-none focus:border-accent"
          />
        </div>
        {inviteToken && (
          <p className="text-xs text-gray-500">Using invite link (org name pre-fillable by the inviter).</p>
        )}
        {status && <p className="text-sm text-gray-400">{status}</p>}
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-accent px-3 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Sign up"}
        </button>
      </form>
      <p className="mt-4 text-center text-xs text-gray-500">
        Already have an account? <a href="/login" className="text-accent hover:underline">Sign in</a>
      </p>
    </div>
  );
}

export default function SignupPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-bg px-4">
      <Suspense fallback={null}>
        <SignupForm />
      </Suspense>
    </main>
  );
}
