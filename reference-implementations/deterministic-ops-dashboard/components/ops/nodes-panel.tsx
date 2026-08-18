import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { NODES } from "@/lib/ops-data";
import { NodeStatusBadge } from "./status-badge";

export function NodesPanel() {
  return (
    <div className="rounded-lg border border-border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Node</TableHead>
            <TableHead>Region</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">CPU</TableHead>
            <TableHead className="text-right">Memory</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {NODES.map((node) => (
            <TableRow key={node.id}>
              <TableCell className="font-medium">{node.name}</TableCell>
              <TableCell className="text-muted-foreground">{node.region}</TableCell>
              <TableCell>
                <NodeStatusBadge status={node.status} />
              </TableCell>
              <TableCell className="text-right tabular-nums">{node.cpuPct}%</TableCell>
              <TableCell className="text-right tabular-nums">{node.memPct}%</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
