import { AlertTriangle, CheckCircle2, CircleDot, Loader2, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { NodeStatus, OpsJob } from "@/lib/ops-data";
import type { EntityStatus } from "@/lib/entity-types";
import { cn } from "@/lib/utils";

const NODE_STATUS_META: Record<NodeStatus, { label: string; className: string; Icon: typeof CheckCircle2 }> = {
  good: {
    label: "Healthy",
    className: "border-transparent bg-[#0ca30c]/15 text-[#3fd43f] dark:text-[#3fd43f]",
    Icon: CheckCircle2,
  },
  warning: {
    label: "Degraded",
    className: "border-transparent bg-[#fab219]/15 text-[#fab219]",
    Icon: AlertTriangle,
  },
  critical: {
    label: "Critical",
    className: "border-transparent bg-[#d03b3b]/15 text-[#f27272]",
    Icon: XCircle,
  },
};

export function NodeStatusBadge({ status }: { status: NodeStatus }) {
  const meta = NODE_STATUS_META[status];
  const Icon = meta.Icon;
  return (
    <Badge className={cn("gap-1.5 font-medium", meta.className)}>
      <Icon className="size-3.5" aria-hidden="true" />
      {meta.label}
    </Badge>
  );
}

const JOB_STATUS_META: Record<OpsJob["status"], { label: string; className: string; Icon: typeof CheckCircle2 }> = {
  succeeded: {
    label: "Succeeded",
    className: "border-transparent bg-[#0ca30c]/15 text-[#3fd43f]",
    Icon: CheckCircle2,
  },
  running: {
    label: "Running",
    className: "border-transparent bg-[#3987e5]/15 text-[#7cabf0]",
    Icon: Loader2,
  },
  failed: {
    label: "Failed",
    className: "border-transparent bg-[#d03b3b]/15 text-[#f27272]",
    Icon: XCircle,
  },
  queued: {
    label: "Queued",
    className: "border-transparent bg-muted text-muted-foreground",
    Icon: CircleDot,
  },
};

export function JobStatusBadge({ status }: { status: OpsJob["status"] }) {
  const meta = JOB_STATUS_META[status];
  const Icon = meta.Icon;
  return (
    <Badge className={cn("gap-1.5 font-medium", meta.className)}>
      <Icon className={cn("size-3.5", status === "running" && "animate-spin")} aria-hidden="true" />
      {meta.label}
    </Badge>
  );
}

/**
 * Badge for the entity graph's real three-state lifecycle
 * (`healthy | degraded | down`, from `lib/entity-types.ts`) — distinct from
 * `NodeStatus`'s `good/warning/critical` labels above, same visual system.
 */
export const ENTITY_STATUS_META: Record<EntityStatus, { label: string; className: string; Icon: typeof CheckCircle2 }> = {
  healthy: {
    label: "Healthy",
    className: "border-transparent bg-[#0ca30c]/15 text-[#3fd43f]",
    Icon: CheckCircle2,
  },
  degraded: {
    label: "Degraded",
    className: "border-transparent bg-[#fab219]/15 text-[#fab219]",
    Icon: AlertTriangle,
  },
  down: {
    label: "Down",
    className: "border-transparent bg-[#d03b3b]/15 text-[#f27272]",
    Icon: XCircle,
  },
};

export function EntityStatusBadge({ status }: { status: EntityStatus }) {
  const meta = ENTITY_STATUS_META[status];
  const Icon = meta.Icon;
  return (
    <Badge className={cn("gap-1.5 font-medium", meta.className)}>
      <Icon className="size-3.5" aria-hidden="true" />
      {meta.label}
    </Badge>
  );
}
