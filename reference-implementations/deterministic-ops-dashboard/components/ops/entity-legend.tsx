import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { Entity, EntityStatus } from "@/lib/entity-types";
import { ENTITY_STATUS_META } from "./status-badge";

const STATUS_ORDER: EntityStatus[] = ["healthy", "degraded", "down"];

// Same swatch colors ENTITY_STATUS_META's badge classes use, duplicated here
// only because a CSS background-color swatch needs a real color value, not
// a Tailwind class string, to draw the dot.
const STATUS_DOT_HEX: Record<EntityStatus, string> = {
  healthy: "#0ca30c",
  degraded: "#fab219",
  down: "#d03b3b",
};

/**
 * Corner-docked legend: maps every real STATUS_COLOR swatch to its status
 * meaning, and computes the real metric min/max from the actual entity list
 * passed in (never hardcoded) since node radius encodes `entity.metric`.
 */
export function EntityLegend({ entities }: { entities: Entity[] }) {
  const metrics = entities.map((e) => e.metric);
  const min = metrics.length ? Math.min(...metrics) : 0;
  const max = metrics.length ? Math.max(...metrics) : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Legend</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-col gap-1.5 text-sm">
          {STATUS_ORDER.map((status) => (
            <span key={status} className="inline-flex items-center gap-2">
              <span
                className="inline-block size-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: STATUS_DOT_HEX[status] }}
                aria-hidden="true"
              />
              {ENTITY_STATUS_META[status].label}
            </span>
          ))}
          <span className="inline-flex items-center gap-2">
            <span className="inline-block h-0.5 w-4 shrink-0 rounded-full bg-[#3987e5]" aria-hidden="true" />
            Call flow (width = traffic share)
          </span>
        </div>
        <Separator />
        <div className="flex flex-col gap-1 text-sm">
          <span className="text-muted-foreground">Node size = metric</span>
          <span className="tabular-nums">
            min {min} · max {max}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
