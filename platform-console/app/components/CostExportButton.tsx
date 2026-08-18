"use client";

import { Button } from "@/components/ui/button";

// Re-declared row shape rather than a runtime import from @/lib/cost --
// lib/cost.ts transitively pulls in lib/k8s.ts (fs/https), which must
// never end up in the client bundle. Only the plain data this component
// actually renders is passed in as props, same "import type only from
// server-only libs" convention components/BudgetAlertsPanel.tsx documents.
export interface CostExportRow {
  namespace: string;
  cpuCoreHours: number | null;
  memoryGiBHours: number | null;
  totalCost: number | null;
  budgetThreshold: number | null;
  status: string;
}

/**
 * Client-side CSV export of exactly the rows already rendered on the page
 * -- no second fetch, no re-derived numbers. Builds a Blob from the same
 * data the table shows and triggers a same-origin download via a
 * temporary <a download>; nothing is sent to any server, and no dollar
 * figure here differs from what's on screen (that's what
 * 'cost-dashboard-renders-live-billing-data' verifies).
 */
export default function CostExportButton({
  rows,
  windowLabel,
}: {
  rows: CostExportRow[];
  windowLabel: string;
}) {
  function onExport() {
    const header = [
      "namespace",
      "cpu_core_hours",
      "total_cost_usd_illustrative",
      "budget_threshold_usd",
      "status",
    ];
    const lines = rows.map((r) =>
      [
        r.namespace,
        r.cpuCoreHours ?? "",
        r.totalCost ?? "",
        r.budgetThreshold ?? "",
        r.status,
      ]
        .map((v) => `"${String(v).replace(/"/g, '""')}"`)
        .join(","),
    );
    const csv = [header.join(","), ...lines].join("\n") + "\n";
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `platform-cost-${windowLabel}-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <Button variant="outline" size="sm" onClick={onExport}>
      Export CSV
    </Button>
  );
}
