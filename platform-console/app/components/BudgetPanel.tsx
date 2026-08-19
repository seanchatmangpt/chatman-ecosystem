"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { ProjectBudgetStatus } from "@/lib/quota-enforcement";

interface Props {
  projectName: string;
  canEdit: boolean; // owner
  initialStatus: ProjectBudgetStatus;
}

/**
 * Per-project FinOps hard-cap panel (control: cost-budget-hard-stop) --
 * the block-not-just-alert counterpart to lib/cost-anomaly.ts's alert-only
 * detector. Same client-component/fetch-then-router.refresh() convention
 * as RedisCachePanel: every state change shown here follows a real 2xx
 * response from app/api/projects/[name]/budget/route.ts, never a
 * locally-fabricated "saved".
 *
 * When the real, server-computed `overBudget` flag is true (hard stop
 * enabled AND current spend >= the configured monthly budget), this
 * renders the same destructive-Alert "blocked" banner shape the rest of
 * this codebase uses for a hard-enforced ceiling (see
 * lib/quota-enforcement.ts's own enforced-namespace state) -- new
 * resource creation for this project's namespace is actually rejected
 * (402) by POST /api/projects, not merely flagged here.
 */
export default function BudgetPanel({ projectName, canEdit, initialStatus }: Props) {
  const router = useRouter();
  const [status, setStatus] = useState(initialStatus);
  const [monthlyBudgetUsd, setMonthlyBudgetUsd] = useState(
    initialStatus.config ? String(initialStatus.config.monthlyBudgetUsd) : "",
  );
  const [hardStop, setHardStop] = useState(initialStatus.config?.hardStop ?? false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function doSave() {
    setBusy(true);
    setError(null);
    try {
      const parsed = Number(monthlyBudgetUsd);
      if (!Number.isFinite(parsed) || parsed <= 0) {
        throw new Error("monthly budget must be a positive number");
      }
      const res = await fetch(`/api/projects/${encodeURIComponent(projectName)}/budget`, {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ monthlyBudgetUsd: parsed, hardStop }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body.error ?? `HTTP ${res.status}`);
      setStatus((prev) => ({ ...prev, config: body.budget }));
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base font-medium">Monthly Budget</CardTitle>
        {status.config ? (
          <Badge variant={status.config.hardStop ? "default" : "outline"}>
            {status.config.hardStop ? "Hard stop enabled" : "Alert only"}
          </Badge>
        ) : (
          <Badge variant="outline">Not configured</Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Real hard cap on this project&apos;s namespace: when hard stop is
          enabled and measured spend reaches the budget, new resource
          creation (<code>POST /api/projects</code>) is rejected with a 402,
          not merely flagged -- distinct from the alert-only
          cost-anomaly detector and overage billing, neither of which
          blocks.
        </p>

        {status.overBudget && (
          <Alert variant="destructive">
            <AlertDescription>
              blocked: budget exceeded -- current spend $
              {status.currentSpendUsd?.toFixed(2)} has reached the ${status.config?.monthlyBudgetUsd.toFixed(2)}{" "}
              monthly hard cap. New resource creation for this project&apos;s
              namespace is being rejected until the budget is raised or the
              hard stop is disabled.
            </AlertDescription>
          </Alert>
        )}

        {status.spendError && (
          <Alert className="border-amber-900 bg-amber-950/40 text-amber-300">
            <AlertDescription className="text-amber-300">
              spend measurement unavailable: {status.spendError}
            </AlertDescription>
          </Alert>
        )}

        <dl className="divide-y divide-border text-sm">
          <div className="grid grid-cols-3 gap-4 py-2">
            <dt className="text-muted-foreground">Current spend (illustrative)</dt>
            <dd className="col-span-2">
              {status.currentSpendUsd !== null ? `$${status.currentSpendUsd.toFixed(2)}` : "unavailable"}
            </dd>
          </div>
          <div className="grid grid-cols-3 gap-4 py-2">
            <dt className="text-muted-foreground">Configured budget</dt>
            <dd className="col-span-2">
              {status.config ? `$${status.config.monthlyBudgetUsd.toFixed(2)} / month` : "none set"}
            </dd>
          </div>
        </dl>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {canEdit && (
          <div className="space-y-3 border-t border-border pt-4">
            <div className="space-y-1">
              <Label htmlFor="monthly-budget-usd">Monthly budget (USD)</Label>
              <Input
                id="monthly-budget-usd"
                type="number"
                min="0"
                step="0.01"
                value={monthlyBudgetUsd}
                onChange={(e) => setMonthlyBudgetUsd(e.target.value)}
                disabled={busy}
                placeholder="e.g. 500"
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={hardStop}
                onChange={(e) => setHardStop(e.target.checked)}
                disabled={busy}
                className="h-4 w-4 rounded border-input"
              />
              Hard stop: block new resource creation once budget is exhausted
            </label>
            <Button onClick={doSave} disabled={busy}>
              {busy ? "Saving..." : "Save budget"}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
