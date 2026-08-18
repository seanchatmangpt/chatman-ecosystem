import { AlertTriangle, ShieldAlert } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { INCIDENTS } from "@/lib/ops-data";

const ICON = {
  warning: AlertTriangle,
  critical: ShieldAlert,
} as const;

export function IncidentsPanel() {
  if (INCIDENTS.length === 0) {
    return <p className="text-sm text-muted-foreground">No open incidents.</p>;
  }

  return (
    <div className="flex flex-col gap-3">
      {INCIDENTS.map((incident) => {
        const Icon = ICON[incident.severity];
        return (
          <Alert
            key={incident.id}
            variant={incident.severity === "critical" ? "destructive" : "default"}
          >
            <Icon className="size-4" />
            <AlertTitle className="flex items-center justify-between gap-2">
              <span>{incident.title}</span>
              <span className="font-mono text-xs font-normal text-muted-foreground">
                {incident.id}
              </span>
            </AlertTitle>
            <AlertDescription>{incident.detail}</AlertDescription>
          </Alert>
        );
      })}
    </div>
  );
}
