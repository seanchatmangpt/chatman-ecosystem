import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Entity } from "@/lib/entity-types";
import { EntityStatusBadge } from "./status-badge";

/**
 * Plain-table view of the SAME entity list the deck.gl canvas renders — same
 * data, two real views. Row click sets selection, same `selectedId` state
 * the canvas and command palette drive.
 */
export function EntityTable({
  entities,
  selectedId,
  onSelect,
}: {
  entities: Entity[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="rounded-lg border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Entity</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Metric</TableHead>
            <TableHead>Calls</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {entities.map((entity) => (
            <TableRow
              key={entity.id}
              data-state={entity.id === selectedId ? "selected" : undefined}
              className="cursor-pointer"
              onClick={() => onSelect(entity.id)}
            >
              <TableCell>
                <div className="font-medium">{entity.label}</div>
                <div className="font-mono text-xs text-muted-foreground">{entity.id}</div>
              </TableCell>
              <TableCell>
                <EntityStatusBadge status={entity.status} />
              </TableCell>
              <TableCell className="text-right tabular-nums">{entity.metric}</TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {entity.edges.length === 0 ? "—" : entity.edges.map((e) => e.targetId).join(", ")}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
