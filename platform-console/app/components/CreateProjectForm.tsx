"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * POSTs a real Project custom resource via /api/projects -> lib/k8s.ts.
 * No client-side simulation of "success" -- the form shows whatever the
 * k8s API actually returned (including a real admission-webhook or
 * validation error) and only clears/refreshes on a real 201.
 */
export default function CreateProjectForm({ namespaces }: { namespaces: string[] }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [namespace, setNamespace] = useState(namespaces[0] ?? "");
  const [dbStorageSize, setDbStorageSize] = useState("1Gi");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, namespace, dbStorageSize }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSuccess(`Created Project/${body.project.name} in namespace ${body.project.namespace}`);
      setName("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card space-y-4 p-6">
      <h2 className="text-base font-medium text-white">Create project</h2>
      <p className="text-xs text-gray-500">
        Submits a real <code>SingleDatabase</code> and a paired{" "}
        <code>Project</code> custom resource (both{" "}
        <code>core.supabase.io/v1alpha1</code>) to the cluster via the
        console&apos;s ServiceAccount. Reconciliation is handled by the
        supabase-operator already running in <code>supabase-system</code> --
        if the target namespace doesn&apos;t exist, or reconciliation hits an
        error, the operator will report that on the project itself (visible
        on its detail page), not fabricated here.
      </p>
      <div className="grid gap-4 sm:grid-cols-3">
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Name</span>
          <input
            required
            pattern="[a-z0-9]([-a-z0-9]*[a-z0-9])?"
            title="lowercase alphanumeric and '-', RFC 1123 label"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            placeholder="my-project"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Target namespace</span>
          <input
            required
            list="namespace-options"
            pattern="[a-z0-9]([-a-z0-9]*[a-z0-9])?"
            value={namespace}
            onChange={(e) => setNamespace(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            placeholder="supabase-demo"
          />
          <datalist id="namespace-options">
            {namespaces.map((ns) => (
              <option key={ns} value={ns} />
            ))}
          </datalist>
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">DB storage size</span>
          <input
            pattern="[0-9]+(\.[0-9]+)?(Ei|Pi|Ti|Gi|Mi|Ki|E|P|T|G|M|k)?"
            title="Kubernetes quantity, e.g. 1Gi"
            value={dbStorageSize}
            onChange={(e) => setDbStorageSize(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            placeholder="1Gi"
          />
        </label>
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Creating..." : "Create project"}
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
  );
}
