"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

interface KeyValuePair {
  key: string;
  value: string;
}

/**
 * POSTs a real k8s Secret via /api/secrets -> lib/k8s.ts. Plaintext values
 * live only in this component's local form state and the single fetch()
 * body that carries them to the API route -- never logged, never written
 * anywhere else client-side. No client-side simulation of "success": the
 * form shows whatever the k8s API actually returned and only clears/
 * refreshes on a real 201.
 */
export default function CreateSecretForm({ namespaces }: { namespaces: string[] }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [namespace, setNamespace] = useState(namespaces[0] ?? "");
  const [pairs, setPairs] = useState<KeyValuePair[]>([{ key: "", value: "" }]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function updatePair(index: number, field: "key" | "value", value: string) {
    setPairs((prev) => prev.map((p, i) => (i === index ? { ...p, [field]: value } : p)));
  }

  function addPair() {
    setPairs((prev) => [...prev, { key: "", value: "" }]);
  }

  function removePair(index: number) {
    setPairs((prev) => prev.filter((_, i) => i !== index));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const data: Record<string, string> = {};
      for (const p of pairs) {
        if (p.key.trim()) data[p.key.trim()] = p.value;
      }
      const res = await fetch("/api/secrets", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name, namespace, data }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setSuccess(`Created Secret/${body.secret.name} in namespace ${body.secret.namespace} with keys: ${body.secret.keys.join(", ")}`);
      setName("");
      setPairs([{ key: "", value: "" }]);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="card space-y-4 p-6">
      <h2 className="text-base font-medium text-white">Create secret</h2>
      <p className="text-xs text-gray-500">
        Submits a real <code>Secret</code> (<code>type: Opaque</code>) to the
        cluster via the console&apos;s ServiceAccount, base64-encoding each
        value as the Kubernetes Secret API requires. Values are never
        logged and never rendered back in this UI once saved -- only key
        names are shown after creation.
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Name</span>
          <input
            required
            pattern="[a-z0-9]([-a-z0-9]*[a-z0-9])?"
            title="lowercase alphanumeric and '-', RFC 1123 label"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
            placeholder="my-api-key"
          />
        </label>
        <label className="block text-sm">
          <span className="mb-1 block text-gray-400">Namespace</span>
          <select
            required
            value={namespace}
            onChange={(e) => setNamespace(e.target.value)}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
          >
            {namespaces.map((ns) => (
              <option key={ns} value={ns}>
                {ns}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="space-y-2">
        <span className="block text-sm text-gray-400">Key / value pairs</span>
        {pairs.map((pair, i) => (
          <div key={i} className="flex gap-2">
            <input
              required
              value={pair.key}
              onChange={(e) => updatePair(i, "key", e.target.value)}
              className="w-1/3 rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder="key"
            />
            <input
              required
              type="password"
              value={pair.value}
              onChange={(e) => updatePair(i, "value", e.target.value)}
              className="flex-1 rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder="value"
              autoComplete="off"
            />
            <button
              type="button"
              onClick={() => removePair(i)}
              disabled={pairs.length === 1}
              className="rounded-md border border-border px-3 py-2 text-xs text-gray-400 hover:text-white disabled:opacity-30"
            >
              Remove
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={addPair}
          className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-300 hover:text-white"
        >
          + Add pair
        </button>
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {submitting ? "Creating..." : "Create secret"}
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
