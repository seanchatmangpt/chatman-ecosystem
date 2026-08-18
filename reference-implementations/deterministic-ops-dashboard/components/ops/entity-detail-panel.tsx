import { MousePointerClick } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Entity } from "@/lib/entity-types";
import { EntityStatusBadge } from "./status-badge";

/**
 * Docked side panel for the currently selected entity. `entity` is driven by
 * whichever real interaction last set selection: a deck.gl node click, a
 * table row click, or Enter in the command palette — all three funnel into
 * the same `selectedId` state in `EntityDashboard`, so this panel is always
 * showing genuinely selected data, never a stub.
 */
export function EntityDetailPanel({ entity }: { entity: Entity | null }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between gap-2 text-sm">
          Selected entity
          {entity && <EntityStatusBadge status={entity.status} />}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!entity ? (
          <p className="flex items-start gap-2 text-sm text-muted-foreground">
            <MousePointerClick className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            Click a node on the map, a row in the table, or press{" "}
            <kbd className="rounded border border-border bg-muted px-1 py-0.5 font-mono text-xs">⌘K</kbd> to
            select an entity.
          </p>
        ) : (
          <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-muted-foreground">Label</dt>
            <dd className="font-medium">{entity.label}</dd>

            <dt className="text-muted-foreground">ID</dt>
            <dd className="font-mono text-xs">{entity.id}</dd>

            <dt className="text-muted-foreground">Status</dt>
            <dd>
              <EntityStatusBadge status={entity.status} />
            </dd>

            <dt className="text-muted-foreground">Metric</dt>
            <dd className="tabular-nums">{entity.metric}</dd>

            <dt className="text-muted-foreground">Calls</dt>
            <dd>
              {entity.edges.length === 0 ? (
                <span className="text-muted-foreground">none</span>
              ) : (
                <ul className="flex flex-col gap-1">
                  {entity.edges.map((edge) => (
                    <li key={edge.targetId} className="tabular-nums">
                      → {edge.targetId}{" "}
                      <span className="text-muted-foreground">({Math.round(edge.weight * 100)}%)</span>
                    </li>
                  ))}
                </ul>
              )}
            </dd>
          </dl>
        )}
      </CardContent>
    </Card>
  );
}
