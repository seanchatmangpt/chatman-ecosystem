import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

export function StatTile({
  label,
  value,
  suffix,
  icon: Icon,
  tone = "default",
}: {
  label: string;
  value: string | number;
  suffix?: string;
  icon: LucideIcon;
  tone?: "default" | "good" | "warning" | "critical";
}) {
  const toneClass = {
    default: "text-foreground",
    good: "text-[#3fd43f]",
    warning: "text-[#fab219]",
    critical: "text-[#f27272]",
  }[tone];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <div className={cn("text-2xl font-semibold tabular-nums", toneClass)}>
          {value}
          {suffix ? <span className="ml-1 text-base font-normal text-muted-foreground">{suffix}</span> : null}
        </div>
      </CardContent>
    </Card>
  );
}
