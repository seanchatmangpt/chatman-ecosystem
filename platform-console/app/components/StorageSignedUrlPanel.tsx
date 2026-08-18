"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * Content/IP protection UI (control: storage-signed-url-expiry-enforced):
 * mints a real, time-boxed HMAC-signed download URL via POST
 * /api/projects/[name]/storage -> lib/storage-signed-url.ts, and links
 * straight to the real download route
 * (/api/projects/[name]/storage/download?token=...) that verifies and
 * enforces that expiry server-side. No client-side simulation of "signed"
 * -- a link only appears after a real 201 from the API route, same
 * "no optimistic UI" convention components/ApiKeysPanel.tsx already
 * follows for its own "shown once" secret value.
 */
export default function StorageSignedUrlPanel({ projectName }: { projectName: string }) {
  const [bucket, setBucket] = useState("");
  const [path, setPath] = useState("");
  const [ttlSeconds, setTtlSeconds] = useState(300);
  const [signing, setSigning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ url: string; expiresAt: string } | null>(null);

  async function onSign(e: React.FormEvent) {
    e.preventDefault();
    setSigning(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/storage`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ bucket, path, ttlSeconds }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? body.reason ?? `HTTP ${res.status}`);
        return;
      }
      setResult({ url: body.url, expiresAt: body.expiresAt });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSigning(false);
    }
  }

  return (
    <div className="card mt-6 p-6">
      <h2 className="mb-1 text-base font-medium text-white">Signed download link</h2>
      <p className="mb-4 text-sm text-gray-400">
        Mints a real, time-boxed HMAC-signed URL (AWS S3 presigned URL equivalent) for one object
        in one bucket. Every access -- expired or valid -- is written to the durable audit trail
        (<code>GET /api/audit</code>).
      </p>

      <form onSubmit={onSign} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="sur-bucket">Bucket</Label>
          <Input
            id="sur-bucket"
            value={bucket}
            onChange={(e) => setBucket(e.target.value)}
            placeholder="e.g. dailies"
            required
            className="mt-1"
          />
        </div>
        <div>
          <Label htmlFor="sur-path">Object path</Label>
          <Input
            id="sur-path"
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="e.g. reel-3/shot-042.mov"
            required
            className="mt-1"
          />
        </div>
        <div>
          <Label htmlFor="sur-ttl">Expires in (seconds)</Label>
          <Input
            id="sur-ttl"
            type="number"
            min={30}
            max={86400}
            value={ttlSeconds}
            onChange={(e) => setTtlSeconds(Number(e.target.value))}
            className="mt-1"
          />
        </div>
        <div className="flex items-end">
          <Button type="submit" disabled={signing}>
            {signing ? "Signing..." : "Generate signed link"}
          </Button>
        </div>
      </form>

      {error && (
        <p className="mt-4 break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-sm text-red-300">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-4 space-y-1 rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-300">
          <p>
            expires at <code>{new Date(result.expiresAt).toLocaleString()}</code>
          </p>
          <code className="block break-all rounded-md border border-border bg-bg px-3 py-2 text-xs text-white">
            {typeof window !== "undefined" ? window.location.origin : ""}
            {result.url}
          </code>
        </div>
      )}
    </div>
  );
}
