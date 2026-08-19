"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface ExportSummary {
  backupJobName: string | null;
  dumpBytes: number;
  buckets: Array<{ name: string; objectCount: number; totalBytes: number }>;
  auditRowCount: number;
  warnings: string[];
}

export default function ExportAllButton({ projectName }: { projectName: string }) {
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    url: string;
    expiresAt: string;
    filename: string;
    archiveBytes: number;
    summary: ExportSummary;
  } | null>(null);

  async function onExport() {
    setRunning(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/export-all`, {
        method: "POST",
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      setResult(body);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-3">
      <Button type="button" onClick={onExport} disabled={running}>
        {running ? "Building export (this triggers a real backup)..." : "Export everything (offboarding bundle)"}
      </Button>

      {error && (
        <p className="max-w-xl break-all rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}

      {result && (
        <div className="max-w-xl space-y-2 rounded-md border border-emerald-900 bg-emerald-950/40 px-3 py-2 text-xs text-emerald-300">
          <p>
            {result.filename} ({(result.archiveBytes / 1024).toFixed(1)} KiB) -- link expires{" "}
            {new Date(result.expiresAt).toLocaleString()}
          </p>
          <a
            href={result.url}
            className="block break-all rounded-md border border-border bg-bg px-3 py-2 text-white underline"
          >
            Download {result.filename}
          </a>
          <ul className="list-disc space-y-0.5 pl-4 text-emerald-200/90">
            <li>
              DB dump: {result.summary.backupJobName ?? "none"} ({result.summary.dumpBytes} bytes)
            </li>
            <li>
              Storage:{" "}
              {result.summary.buckets.length === 0
                ? "no buckets"
                : result.summary.buckets
                    .map((b) => `${b.name} (${b.objectCount} objects, ${b.totalBytes} bytes)`)
                    .join(", ")}
            </li>
            <li>Audit log rows: {result.summary.auditRowCount}</li>
          </ul>
          {result.summary.warnings.length > 0 && (
            <ul className="list-disc space-y-0.5 pl-4 text-amber-300">
              {result.summary.warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
