"use client";

import Link from "next/link";
import { useState } from "react";
import type { TaggableResourceType } from "@/lib/tags";

interface TaggedResource {
  type: TaggableResourceType;
  name: string;
  namespace: string;
  detail: string;
  path: string;
}

const TYPE_LABEL: Record<TaggableResourceType, string> = {
  service: "Service",
  project: "Project",
  cronjob: "Scheduled Job",
  "feature-flags": "Feature Flags",
  webhooks: "Webhooks",
};

// Same 5 platform namespaces app/service-discovery/page.tsx and
// lib/scheduled-jobs.ts's SCHEDULABLE_NAMESPACES already use for their own
// namespace pickers -- duplicated here for the same reason
// lib/global-search.ts's own header comment documents for
// SECRET_NAMESPACES.
const SERVICE_PROJECT_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
];
const CRONJOB_NAMESPACES = ["autofde-lab", "gymact", "ggen", "ggen-marketplace", "supabase-demo"];

function namespaceOptionsFor(type: TaggableResourceType): string[] {
  return type === "cronjob" ? CRONJOB_NAMESPACES : SERVICE_PROJECT_NAMESPACES;
}

function needsRef(type: TaggableResourceType): boolean {
  return type !== "feature-flags" && type !== "webhooks";
}

/**
 * The /tags page's own client: a real "browse by tag" search hitting
 * GET /api/tags?key=&value= (lib/tags.ts's listResourcesByTag -- a real
 * `?labelSelector=` query against the k8s API per category, never a
 * client-side filter), plus a generic "apply a tag" form covering every
 * taggable category (Services/Projects/Scheduled Jobs by namespace+name,
 * Feature Flags/Webhooks as fixed singleton ConfigMaps) hitting
 * POST /api/tags (lib/tags.ts's applyTag -- a real RFC 7386 label merge
 * patch). No optimistic UI: results only reflect what the API just
 * returned from a real, live request.
 */
export default function TagsBrowser() {
  const [browseKey, setBrowseKey] = useState("");
  const [browseValue, setBrowseValue] = useState("");
  const [results, setResults] = useState<TaggedResource[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [applyType, setApplyType] = useState<TaggableResourceType>("service");
  const [applyNamespace, setApplyNamespace] = useState(SERVICE_PROJECT_NAMESPACES[0]);
  const [applyName, setApplyName] = useState("");
  const [applyKey, setApplyKey] = useState("");
  const [applyValue, setApplyValue] = useState("");
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applySuccess, setApplySuccess] = useState<string | null>(null);

  async function runSearch(e: React.FormEvent) {
    e.preventDefault();
    const key = browseKey.trim();
    const value = browseValue.trim();
    if (!key || !value) return;
    setSearching(true);
    setSearchError(null);
    try {
      const qs = new URLSearchParams({ key, value });
      const res = await fetch(`/api/tags?${qs.toString()}`);
      const body = await res.json();
      if (!res.ok) {
        setSearchError(body.error ?? `HTTP ${res.status}`);
        setResults(null);
        return;
      }
      setResults(body.resources as TaggedResource[]);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : String(err));
      setResults(null);
    } finally {
      setSearching(false);
    }
  }

  function onTypeChange(type: TaggableResourceType) {
    setApplyType(type);
    setApplyNamespace(namespaceOptionsFor(type)[0]);
    setApplyName("");
    setApplyError(null);
    setApplySuccess(null);
  }

  async function submitApply(e: React.FormEvent) {
    e.preventDefault();
    const key = applyKey.trim();
    const value = applyValue.trim();
    if (!key || !value) return;
    if (needsRef(applyType) && !applyName.trim()) {
      setApplyError("name is required");
      return;
    }
    setApplying(true);
    setApplyError(null);
    setApplySuccess(null);
    try {
      const res = await fetch("/api/tags", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          resourceType: applyType,
          namespace: applyNamespace,
          name: applyName.trim(),
          key,
          value,
        }),
      });
      const body = await res.json();
      if (!res.ok) {
        setApplyError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setApplySuccess(
        `Applied ${key}=${value} to ${TYPE_LABEL[applyType]} ${needsRef(applyType) ? `${applyNamespace}/${applyName}` : ""}.`,
      );
      setApplyKey("");
      setApplyValue("");
    } catch (err) {
      setApplyError(err instanceof Error ? err.message : String(err));
    } finally {
      setApplying(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-foreground">Browse by tag</h2>
        <p className="text-xs text-muted-foreground">
          Real cross-resource lookup: every category is queried live via the k8s API&apos;s own{" "}
          <code>?labelSelector=</code> query parameter for exactly{" "}
          <code>platform-console.io/tag-&lt;key&gt;=&lt;value&gt;</code> -- a genuine server-side
          filter, never a client-side scan of every resource on the cluster.
        </p>
        <form onSubmit={runSearch} className="flex flex-wrap items-end gap-3">
          <label className="block text-sm">
            <span className="mb-1 block text-muted-foreground">Key</span>
            <input
              value={browseKey}
              onChange={(e) => setBrowseKey(e.target.value)}
              placeholder="env"
              className="w-40 rounded-md border border-border bg-bg px-3 py-2 text-sm text-foreground"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-muted-foreground">Value</span>
            <input
              value={browseValue}
              onChange={(e) => setBrowseValue(e.target.value)}
              placeholder="production"
              className="w-40 rounded-md border border-border bg-bg px-3 py-2 text-sm text-foreground"
            />
          </label>
          <button
            type="submit"
            disabled={searching || !browseKey.trim() || !browseValue.trim()}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {searching ? "Searching..." : "Search"}
          </button>
        </form>

        {searchError && (
          <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
            {searchError}
          </p>
        )}

        {results !== null && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              {results.length} resource(s) match <code>{browseKey}={browseValue}</code>.
            </p>
            {results.length > 0 && (
              <div className="divide-y divide-border rounded-md border border-border">
                {results.map((r) => (
                  <div
                    key={`${r.type}-${r.namespace}-${r.name}`}
                    className="flex items-center justify-between gap-4 px-4 py-2.5"
                  >
                    <div className="min-w-0">
                      <Link href={r.path} className="text-sm text-foreground hover:text-accent">
                        {r.name}
                      </Link>
                      <p className="truncate text-xs text-muted-foreground">{r.detail}</p>
                    </div>
                    <span className="shrink-0 rounded border border-border px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
                      {TYPE_LABEL[r.type]}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <form onSubmit={submitApply} className="card space-y-4 p-6">
        <h2 className="text-base font-medium text-foreground">Apply a tag</h2>
        <p className="text-xs text-muted-foreground">
          PATCHes a real k8s label (<code>platform-console.io/tag-&lt;key&gt;: &lt;value&gt;</code>
          ) onto the real object -- a real RFC 7386 merge patch, never a client-side simulation.
          Requires at least the <code>member</code> role (and <code>owner</code> for Webhooks,
          matching Global Search&apos;s own minimum role for that category).
        </p>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block text-muted-foreground">Resource type</span>
            <select
              value={applyType}
              onChange={(e) => onTypeChange(e.target.value as TaggableResourceType)}
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-foreground"
            >
              <option value="service">Service</option>
              <option value="project">Project</option>
              <option value="cronjob">Scheduled Job (CronJob)</option>
              <option value="feature-flags">Feature Flags (ConfigMap)</option>
              <option value="webhooks">Webhooks (ConfigMap)</option>
            </select>
          </label>

          {needsRef(applyType) ? (
            <label className="block text-sm">
              <span className="mb-1 block text-muted-foreground">Namespace</span>
              <select
                value={applyNamespace}
                onChange={(e) => setApplyNamespace(e.target.value)}
                className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-foreground"
              >
                {namespaceOptionsFor(applyType).map((ns) => (
                  <option key={ns} value={ns}>
                    {ns}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <label className="block text-sm">
              <span className="mb-1 block text-muted-foreground">Namespace</span>
              <input
                disabled
                value="platform-console (fixed)"
                className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-muted-foreground"
              />
            </label>
          )}

          {needsRef(applyType) ? (
            <label className="block text-sm">
              <span className="mb-1 block text-muted-foreground">Name</span>
              <input
                required
                value={applyName}
                onChange={(e) => setApplyName(e.target.value)}
                placeholder={applyType === "cronjob" ? "my-scheduled-job" : "resource name"}
                className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-foreground"
              />
            </label>
          ) : (
            <label className="block text-sm">
              <span className="mb-1 block text-muted-foreground">Name</span>
              <input
                disabled
                value={
                  applyType === "feature-flags" ? "platform-feature-flags (fixed)" : "platform-console-webhooks (fixed)"
                }
                className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-muted-foreground"
              />
            </label>
          )}

          <label className="block text-sm">
            <span className="mb-1 block text-muted-foreground">Tag key</span>
            <input
              required
              value={applyKey}
              onChange={(e) => setApplyKey(e.target.value)}
              placeholder="env"
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-foreground"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-muted-foreground">Tag value</span>
            <input
              required
              value={applyValue}
              onChange={(e) => setApplyValue(e.target.value)}
              placeholder="production"
              className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-foreground"
            />
          </label>
        </div>
        <button
          type="submit"
          disabled={applying}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {applying ? "Applying..." : "Apply tag"}
        </button>

        {applyError && (
          <p className="break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
            {applyError}
          </p>
        )}
        {applySuccess && (
          <p className="break-all rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-300">
            {applySuccess}
          </p>
        )}
      </form>
    </div>
  );
}
