"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/**
 * Reads/writes the real platform-feature-flags ConfigMap via
 * /api/feature-flags -> lib/k8s.ts's createOrUpdateConfigMap (a real RFC
 * 7386 JSON merge patch, or a real create on first write). No client-side
 * simulation of "toggled" -- a row's displayed value only changes after a
 * real 200 from the API route (router.refresh() re-reads the live
 * ConfigMap server-side, the same "no optimistic UI" convention every
 * other mutating form in this console already follows).
 */
export default function FeatureFlagsPanel({ flags }: { flags: Record<string, string> }) {
  const router = useRouter();
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("false");
  const [creating, setCreating] = useState(false);

  async function setFlag(key: string, value: string) {
    setBusyKey(key);
    setError(null);
    try {
      const res = await fetch("/api/feature-flags", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ key, value }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusyKey(null);
    }
  }

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    const key = newKey.trim();
    if (!key) return;
    setCreating(true);
    await setFlag(key, newValue);
    setCreating(false);
    setNewKey("");
    setNewValue("false");
  }

  const entries = Object.entries(flags).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h2 className="mb-4 text-base font-medium text-white">Flags</h2>
        {entries.length === 0 && (
          <p className="text-sm text-gray-500">
            No flags yet -- the <code>platform-feature-flags</code> ConfigMap does not exist or
            is empty. Add one below.
          </p>
        )}
        {entries.length > 0 && (
          <div className="divide-y divide-border">
            {entries.map(([key, value]) => {
              const isBoolean = value === "true" || value === "false";
              return (
                <div key={key} className="flex items-center justify-between gap-4 py-3">
                  <div>
                    <p className="text-sm font-medium text-white">{key}</p>
                    <p className="text-xs text-gray-500">
                      value: <code>{value}</code>
                    </p>
                  </div>
                  {isBoolean ? (
                    <button
                      type="button"
                      onClick={() => setFlag(key, value === "true" ? "false" : "true")}
                      disabled={busyKey === key}
                      className={`rounded-md border px-3 py-1.5 text-xs disabled:opacity-50 ${
                        value === "true"
                          ? "border-emerald-900 bg-emerald-950/40 text-emerald-300"
                          : "border-border text-gray-300 hover:text-white"
                      }`}
                    >
                      {busyKey === key
                        ? "Toggling..."
                        : value === "true"
                          ? "ON -- toggle off"
                          : "OFF -- toggle on"}
                    </button>
                  ) : (
                    <EditFlagValue
                      currentValue={value}
                      busy={busyKey === key}
                      onSave={(v) => setFlag(key, v)}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <form onSubmit={onCreate} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-white">Add / set flag</h2>
        <p className="text-xs text-gray-500">
          Submits a real <code>ConfigMap</code> merge patch (or create, on first use) via the
          console&apos;s ServiceAccount. An existing key is overwritten in place; a new key is
          added alongside the existing flags -- never a full-map replace.
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Key</span>
            <input
              required
              pattern="[a-zA-Z0-9]([-._a-zA-Z0-9]*[a-zA-Z0-9])?"
              title="a valid ConfigMap data key"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder="verbose-status"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-400">Value</span>
            <input
              required
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-white"
              placeholder="true / false / any string"
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={creating}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {creating ? "Saving..." : "Save flag"}
        </button>
      </form>

      {error && (
        <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </div>
  );
}

function EditFlagValue({
  currentValue,
  busy,
  onSave,
}: {
  currentValue: string;
  busy: boolean;
  onSave: (value: string) => void;
}) {
  const [value, setValue] = useState(currentValue);
  return (
    <div className="flex items-center gap-2">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="w-40 rounded-md border border-border bg-bg px-2 py-1 text-xs text-white"
      />
      <button
        type="button"
        onClick={() => onSave(value)}
        disabled={busy || value === currentValue}
        className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-300 hover:text-white disabled:opacity-30"
      >
        {busy ? "Saving..." : "Save"}
      </button>
    </div>
  );
}
