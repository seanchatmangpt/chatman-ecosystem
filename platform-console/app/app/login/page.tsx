"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function AdminLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.error ?? "sign-in failed");
        setSubmitting(false);
        return;
      }
      router.push(next);
      router.refresh();
    } catch {
      setError("network error while signing in");
      setSubmitting(false);
    }
  }

  return (
    <div className="card w-full max-w-sm p-8">
      <h1 className="mb-1 text-lg font-semibold text-white">Admin sign-in</h1>
      <p className="mb-6 text-sm text-gray-400">
        Single seeded operator account (local credentials).
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-xs text-gray-400" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
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
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white outline-none focus:border-accent"
          />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-accent px-3 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}

function GoTrueLoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";

  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const path =
        mode === "signin" ? "/api/auth/gotrue-login" : "/api/auth/gotrue-signup";
      const res = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        setError(body.error ?? "sign-in failed");
        setSubmitting(false);
        return;
      }
      router.push(next);
      router.refresh();
    } catch {
      setError("network error while signing in");
      setSubmitting(false);
    }
  }

  return (
    <div className="card w-full max-w-sm p-8">
      <h1 className="mb-1 text-lg font-semibold text-white">
        Sign in with your account
      </h1>
      <p className="mb-6 text-sm text-gray-400">
        Real identity federation -- authenticates against the live GoTrue
        (Supabase Auth) instance, independent of the admin account above.
      </p>
      <div className="mb-4 flex gap-2 text-xs">
        <button
          type="button"
          onClick={() => setMode("signin")}
          className={`rounded-md px-2 py-1 ${mode === "signin" ? "bg-accent text-white" : "text-gray-400 hover:text-white"}`}
        >
          Sign in
        </button>
        <button
          type="button"
          onClick={() => setMode("signup")}
          className={`rounded-md px-2 py-1 ${mode === "signup" ? "bg-accent text-white" : "text-gray-400 hover:text-white"}`}
        >
          Create account
        </button>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-xs text-gray-400" htmlFor="gotrue-email">
            Email
          </label>
          <input
            id="gotrue-email"
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
          <label className="mb-1 block text-xs text-gray-400" htmlFor="gotrue-password">
            Password
          </label>
          <input
            id="gotrue-password"
            name="password"
            type="password"
            autoComplete={mode === "signin" ? "current-password" : "new-password"}
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white outline-none focus:border-accent"
          />
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md border border-accent px-3 py-2 text-sm font-medium text-accent hover:bg-accent hover:text-white disabled:opacity-50"
        >
          {submitting
            ? "Please wait..."
            : mode === "signin"
              ? "Sign in"
              : "Create account & sign in"}
        </button>
      </form>
    </div>
  );
}

function LoginPageBody() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4 py-12 lg:flex-row lg:items-start lg:gap-8">
      <AdminLoginForm />
      <GoTrueLoginForm />
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageBody />
    </Suspense>
  );
}
