"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { TaggableResourceType } from "@/lib/tags";

/**
 * Small, reusable tag-editor widget -- embedded directly on a resource's
 * own detail view (Service Discovery's per-Service row, Projects' per-
 * Project row) so tagging never requires leaving that page. Reads/writes
 * the real k8s label via /api/tags -> lib/tags.ts's applyTag/removeTag (a
 * real RFC 7386 merge patch). No client-side simulation of "tagged" -- a
 * tag only appears after a real 200 from the API route
 * (router.refresh() re-reads the live object server-side), the same
 * "no optimistic UI" convention FeatureFlagsPanel already follows.
 */
export default function TagEditor({
  resourceType,
  namespace,
  name,
  initialTags,
}: {
  resourceType: TaggableResourceType;
  namespace: string;
  name: string;
  initialTags: Record<string, string>;
}) {
  const router = useRouter();
  const [key, setKey] = useState("");
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function addTag(e: React.FormEvent) {
    e.preventDefault();
    const k = key.trim();
    const v = value.trim();
    if (!k || !v) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/tags", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ resourceType, namespace, name, key: k, value: v }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setKey("");
      setValue("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function onRemove(tagKey: string) {
    setBusy(true);
    setError(null);
    try {
      const qs = new URLSearchParams({ resourceType, namespace, name, key: tagKey });
      const res = await fetch(`/api/tags?${qs.toString()}`, { method: "DELETE" });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  const entries = Object.entries(initialTags).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="mt-2 space-y-1.5">
      {entries.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {entries.map(([k, v]) => (
            <span
              key={k}
              className="inline-flex items-center gap-1 rounded-full border border-border bg-panel px-2 py-0.5 text-[11px] text-muted-foreground"
            >
              <code>
                {k}={v}
              </code>
              <button
                type="button"
                onClick={() => onRemove(k)}
                disabled={busy}
                className="leading-none text-muted-foreground hover:text-red-400 disabled:opacity-50"
                aria-label={`remove tag ${k}`}
                title={`remove tag ${k}`}
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      )}
      <form onSubmit={addTag} className="flex flex-wrap items-center gap-1.5">
        <input
          value={key}
          onChange={(e) => setKey(e.target.value)}
          placeholder="key"
          className="w-20 rounded-md border border-border bg-bg px-2 py-1 text-[11px] text-foreground"
        />
        <span className="text-muted-foreground">=</span>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="value"
          className="w-24 rounded-md border border-border bg-bg px-2 py-1 text-[11px] text-foreground"
        />
        <button
          type="submit"
          disabled={busy || !key.trim() || !value.trim()}
          className="rounded-md border border-border px-2 py-1 text-[11px] text-muted-foreground hover:text-foreground disabled:opacity-40"
        >
          {busy ? "..." : "+ tag"}
        </button>
      </form>
      {error && <p className="max-w-xs break-all text-[11px] text-red-400">{error}</p>}
    </div>
  );
}
