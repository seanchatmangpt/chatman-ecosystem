"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { JOBS, nodeById, type OpsJob } from "@/lib/ops-data";
import { JobStatusBadge } from "./status-badge";

function formatDuration(ms: number): string {
  if (ms === 0) return "—";
  if (ms < 1000) return `${ms}ms`;
  const s = ms / 1000;
  if (s < 60) return `${s.toFixed(1)}s`;
  return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toISOString().replace("T", " ").replace("Z", " UTC");
}

export function JobsPanel() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return JOBS;
    return JOBS.filter((job) => {
      const node = nodeById(job.nodeId);
      return (
        job.name.toLowerCase().includes(q) ||
        job.id.toLowerCase().includes(q) ||
        (node && (node.name.toLowerCase().includes(q) || node.region.toLowerCase().includes(q)))
      );
    });
  }, [query]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-end gap-3">
        <div className="grid gap-1.5">
          <Label htmlFor="job-filter">Filter jobs</Label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="job-filter"
              placeholder="job name, id, node, or region…"
              className="w-72 pl-8"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
        </div>
        <p className="pb-2 text-sm text-muted-foreground">
          {filtered.length} of {JOBS.length} jobs
        </p>
      </div>

      <div className="rounded-lg border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Job</TableHead>
              <TableHead>Node</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Started</TableHead>
              <TableHead className="text-right">Duration</TableHead>
              <TableHead className="text-right">Retries</TableHead>
              <TableHead className="w-0" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((job) => (
              <JobRow key={job.id} job={job} />
            ))}
            {filtered.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                  No jobs match &ldquo;{query}&rdquo;.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function JobRow({ job }: { job: OpsJob }) {
  const node = nodeById(job.nodeId);
  return (
    <TableRow>
      <TableCell className="font-mono text-xs text-muted-foreground">
        {job.id}
        <div className="font-sans text-sm font-medium text-foreground">{job.name}</div>
      </TableCell>
      <TableCell>{node?.name ?? job.nodeId}</TableCell>
      <TableCell>
        <JobStatusBadge status={job.status} />
      </TableCell>
      <TableCell className="tabular-nums text-muted-foreground">{formatTimestamp(job.startedAt)}</TableCell>
      <TableCell className="text-right tabular-nums">{formatDuration(job.durationMs)}</TableCell>
      <TableCell className="text-right tabular-nums">{job.retries}</TableCell>
      <TableCell>
        <Dialog>
          <DialogTrigger render={<Button variant="ghost" size="sm" />}>
            Details
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-mono text-base">{job.id}</DialogTitle>
              <DialogDescription>{job.name}</DialogDescription>
            </DialogHeader>
            <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2 text-sm">
              <dt className="text-muted-foreground">Node</dt>
              <dd className="tabular-nums">{node?.name ?? job.nodeId} · {node?.region}</dd>
              <dt className="text-muted-foreground">Status</dt>
              <dd>
                <JobStatusBadge status={job.status} />
              </dd>
              <dt className="text-muted-foreground">Started</dt>
              <dd className="tabular-nums">{formatTimestamp(job.startedAt)}</dd>
              <dt className="text-muted-foreground">Duration</dt>
              <dd className="tabular-nums">{formatDuration(job.durationMs)}</dd>
              <dt className="text-muted-foreground">Retries</dt>
              <dd className="tabular-nums">{job.retries}</dd>
              <dt className="text-muted-foreground">Throughput</dt>
              <dd className="tabular-nums">{Math.round(job.throughput * 100)}%</dd>
            </dl>
          </DialogContent>
        </Dialog>
      </TableCell>
    </TableRow>
  );
}
