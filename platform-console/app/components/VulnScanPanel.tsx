"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface ImageOption {
  id: string;
  label: string;
  ref: string;
  source: "containerd" | "remote";
  isControl: boolean;
}

interface VulnFinding {
  pkgName: string;
  installedVersion: string;
  fixedVersion: string | null;
  vulnerabilityId: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN";
  title: string;
}

interface ImageScanResult {
  target: ImageOption;
  pod: string | null;
  phase: string;
  exitReason: string | null;
  findings: VulnFinding[];
  severityCounts: Record<string, number>;
  error: string | null;
}

interface VulnScanRun {
  jobName: string;
  namespace: string;
  createdAt: string | null;
  completions: number;
  succeeded: number;
  failed: number;
  active: number;
  complete: boolean;
  images: ImageScanResult[];
}

type RunStatus = "idle" | "starting" | "polling" | "complete" | "error";

const SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"];
const SEVERITY_COLOR: Record<string, string> = {
  CRITICAL: "text-red-400 border-red-900 bg-red-950/40",
  HIGH: "text-orange-400 border-orange-900 bg-orange-950/40",
  MEDIUM: "text-amber-400 border-amber-900 bg-amber-950/40",
  LOW: "text-sky-400 border-sky-900 bg-sky-950/40",
  UNKNOWN: "text-gray-400 border-gray-800 bg-gray-950/40",
};

const POLL_MS = 3000;

/**
 * Real Container Vulnerability Scanning trigger + live results panel.
 * POSTs `/api/security-scan` to create a real k8s Indexed Job (one real
 * `trivy` pod per image), then polls GET on the same route every
 * `POLL_MS` until every completion index has terminated -- rendering each
 * image's real phase/findings as they land, not a single all-or-nothing
 * wait. Owner-gated server-side (the page and every verb of the API route
 * enforce it independently); this component has no client-side gate to
 * bypass.
 */
export default function VulnScanPanel({ images }: { images: ImageOption[] }) {
  const [status, setStatus] = useState<RunStatus>("idle");
  const [run, setRun] = useState<VulnScanRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]);

  const poll = useCallback(
    async (jobName: string) => {
      try {
        const res = await fetch(`/api/security-scan?jobName=${encodeURIComponent(jobName)}`);
        const body = await res.json();
        if (!res.ok) {
          setError(body.error ?? `HTTP ${res.status}`);
          setStatus("error");
          stopPolling();
          return;
        }
        const nextRun: VulnScanRun = body.run;
        setRun(nextRun);
        if (nextRun.complete) {
          setStatus("complete");
          stopPolling();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setStatus("error");
        stopPolling();
      }
    },
    [stopPolling],
  );

  async function startScan() {
    stopPolling();
    setError(null);
    setRun(null);
    setExpanded({});
    setStatus("starting");
    try {
      const res = await fetch("/api/security-scan", { method: "POST" });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        setStatus("error");
        return;
      }
      setStatus("polling");
      await poll(body.jobName);
      pollRef.current = setInterval(() => poll(body.jobName), POLL_MS);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStatus("error");
    }
  }

  async function cleanup() {
    if (!run) return;
    try {
      await fetch(`/api/security-scan?jobName=${encodeURIComponent(run.jobName)}`, {
        method: "DELETE",
      });
    } catch {
      // best-effort cleanup -- the Job is a fixed-size Indexed Job with a
      // 240s activeDeadlineSeconds, so a failed cleanup here is not a leak.
    }
  }

  const totals = run
    ? run.images.reduce(
        (acc, img) => {
          for (const sev of SEVERITY_ORDER) acc[sev] = (acc[sev] ?? 0) + (img.severityCounts[sev] ?? 0);
          return acc;
        },
        {} as Record<string, number>,
      )
    : null;

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="mb-4 flex items-center gap-3">
          <button
            type="button"
            onClick={startScan}
            disabled={status === "starting" || status === "polling"}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {status === "starting"
              ? "Starting scan..."
              : status === "polling"
                ? "Scanning..."
                : "Run vulnerability scan"}
          </button>
          {run && (
            <span className="text-xs text-gray-400">
              job <code>{run.jobName}</code> -- {run.succeeded}/{run.completions} succeeded
              {run.failed > 0 ? `, ${run.failed} failed` : ""}
              {run.active > 0 ? `, ${run.active} running` : ""}
            </span>
          )}
          {status === "complete" && (
            <button
              type="button"
              onClick={cleanup}
              className="rounded-md border border-border px-3 py-1.5 text-xs text-gray-400 hover:text-white"
            >
              Clean up job
            </button>
          )}
        </div>

        {error && (
          <p className="mb-4 rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
            {error}
          </p>
        )}

        {totals && (
          <div className="mb-4 flex flex-wrap gap-2">
            {SEVERITY_ORDER.map((sev) => (
              <span
                key={sev}
                className={`rounded-md border px-2.5 py-1 text-xs font-medium ${SEVERITY_COLOR[sev]}`}
              >
                {sev}: {totals[sev] ?? 0}
              </span>
            ))}
          </div>
        )}

        {!run && status === "idle" && (
          <p className="text-sm text-gray-500">
            No scan run yet. This will scan {images.filter((i) => !i.isControl).length} of the
            platform&apos;s own images plus 1 positive-control public image.
          </p>
        )}
      </div>

      {(run ? run.images : images.map((i) => ({ target: i, pod: null, phase: "Pending", exitReason: null, findings: [] as VulnFinding[], severityCounts: {}, error: null }))).map(
        (img) => {
          const key = img.target.id;
          const isOpen = expanded[key] ?? false;
          return (
            <div key={key} className="card overflow-hidden">
              <button
                type="button"
                onClick={() => setExpanded((prev) => ({ ...prev, [key]: !prev[key] }))}
                className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left"
              >
                <div>
                  <p className="text-sm font-medium text-white">
                    {img.target.label}
                    {img.target.isControl && (
                      <span className="ml-2 rounded-md border border-purple-900 bg-purple-950/40 px-2 py-0.5 text-[10px] font-medium text-purple-300">
                        POSITIVE CONTROL
                      </span>
                    )}
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    <code>{img.target.ref}</code> -- source: {img.target.source}
                    {img.pod ? ` -- pod: ${img.pod}` : ""}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span
                    className={`rounded-md border px-2 py-1 text-xs ${
                      img.phase === "Succeeded"
                        ? "border-emerald-900 bg-emerald-950/40 text-emerald-300"
                        : img.phase === "Failed"
                          ? "border-red-900 bg-red-950/40 text-red-300"
                          : "border-amber-900 bg-amber-950/40 text-amber-300"
                    }`}
                  >
                    {img.phase}
                  </span>
                  <span className="text-xs text-gray-500">{img.findings.length} findings</span>
                </div>
              </button>

              {img.error && (
                <p className="mx-6 mb-4 rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
                  {img.error}
                </p>
              )}

              {isOpen && img.findings.length > 0 && (
                <div className="max-h-96 overflow-auto border-t border-border">
                  <table className="w-full text-left text-xs">
                    <thead className="sticky top-0 bg-panel text-gray-400">
                      <tr>
                        <th className="px-4 py-2">Severity</th>
                        <th className="px-4 py-2">CVE / Advisory</th>
                        <th className="px-4 py-2">Package</th>
                        <th className="px-4 py-2">Installed</th>
                        <th className="px-4 py-2">Fixed</th>
                        <th className="px-4 py-2">Title</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[...img.findings]
                        .sort(
                          (a, b) =>
                            SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity),
                        )
                        .map((f, i) => (
                          <tr key={`${f.vulnerabilityId}-${f.pkgName}-${i}`} className="border-t border-border/50">
                            <td className="px-4 py-2">
                              <span className={`rounded px-1.5 py-0.5 ${SEVERITY_COLOR[f.severity]}`}>
                                {f.severity}
                              </span>
                            </td>
                            <td className="px-4 py-2 font-mono text-gray-300">{f.vulnerabilityId}</td>
                            <td className="px-4 py-2 text-gray-300">{f.pkgName}</td>
                            <td className="px-4 py-2 text-gray-400">{f.installedVersion}</td>
                            <td className="px-4 py-2 text-gray-400">{f.fixedVersion ?? "--"}</td>
                            <td className="px-4 py-2 text-gray-400">{f.title}</td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}

              {isOpen && img.phase === "Succeeded" && img.findings.length === 0 && (
                <p className="border-t border-border px-6 py-4 text-xs text-emerald-300">
                  Real scan completed -- zero vulnerabilities found in this image&apos;s installed
                  packages against the current trivy-db.
                </p>
              )}
            </div>
          );
        },
      )}
    </div>
  );
}
