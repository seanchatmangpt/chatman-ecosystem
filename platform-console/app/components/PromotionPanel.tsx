"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

// Re-declared as a plain local union (never a runtime import of
// lib/environments.ts, which is fine to import client-side on its own but
// kept local anyway for the same "no accidental pull of a server-only
// module through this component" discipline components/BackupRetentionPanel.tsx
// documents for its own re-declared view type).
type Environment = "dev" | "staging" | "prod";

const NEXT_ENVIRONMENT: Record<Environment, Environment | null> = {
  dev: "staging",
  staging: "prod",
  prod: null,
};

function environmentBadgeClass(environment: Environment): string {
  if (environment === "prod") return "border-red-900 bg-red-950/40 text-red-300";
  if (environment === "staging") return "border-amber-900 bg-amber-950/40 text-amber-300";
  return "border-gray-700 bg-gray-900/40 text-gray-300";
}

/**
 * Real environment-promotion control for one Project -- POSTs
 * app/api/projects/[name]/promote (lib/environments.ts's forward-only
 * dev -> staging -> prod validation, lib/freeze-windows.ts's
 * checkFreezeGuard, lib/approval-workflow.ts's requireApproval gated on
 * `environment.promote`). A 202 here means a second, distinct owner must
 * approve via /api/approvals before the promotion actually applies -- this
 * panel surfaces that pending state rather than pretending the Project
 * already moved, same convention components/BackupRetentionPanel.tsx
 * already establishes for its own maker-checker-gated retention change.
 */
export default function PromotionPanel({
  projectName,
  canManage,
  initialEnvironment,
}: {
  projectName: string;
  canManage: boolean;
  initialEnvironment: Environment;
}) {
  const router = useRouter();
  const [promoting, setPromoting] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const target = NEXT_ENVIRONMENT[initialEnvironment];

  async function onPromote() {
    if (!target) return;
    setPromoting(true);
    setError(null);
    setPendingMessage(null);
    try {
      const res = await fetch(`/api/projects/${projectName}/promote`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ targetEnvironment: target }),
      });
      const body = await res.json();
      if (res.status === 202) {
        setPendingMessage(body.message ?? "promotion is pending a second approver");
        return;
      }
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        return;
      }
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setPromoting(false);
    }
  }

  return (
    <section className="rounded-md border border-gray-800 bg-gray-900/40 px-4 py-4">
      <h2 className="mb-1 text-sm font-medium text-white">Environment promotion</h2>
      <p className="mb-3 flex items-center gap-2 text-xs text-gray-400">
        Current environment:
        <span className={`rounded-full border px-2 py-0.5 text-xs ${environmentBadgeClass(initialEnvironment)}`}>
          {initialEnvironment}
        </span>
      </p>

      {!canManage ? (
        <p className="text-xs text-gray-500">Only an org owner can promote this project.</p>
      ) : target === null ? (
        <p className="text-xs text-gray-500">This project is already at <code>prod</code> -- there is nothing further to promote it to.</p>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-gray-400">Promote to</span>
          <span className={`rounded-full border px-2 py-0.5 text-xs ${environmentBadgeClass(target)}`}>
            {target}
          </span>
          <button
            onClick={onPromote}
            disabled={promoting}
            className="rounded-md border border-gray-700 bg-gray-800 px-3 py-1.5 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
          >
            {promoting ? "Requesting..." : `Promote to ${target}`}
          </button>
        </div>
      )}

      {pendingMessage && (
        <p className="mt-3 rounded-md border border-amber-900 bg-amber-950/40 px-3 py-2 text-xs text-amber-300">
          {pendingMessage}
        </p>
      )}
      {error && (
        <p className="mt-3 rounded-md border border-red-900 bg-red-950/40 px-3 py-2 text-xs text-red-300">
          {error}
        </p>
      )}
    </section>
  );
}
