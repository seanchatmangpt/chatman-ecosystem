"use client";

import { useState } from "react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface LogEntry {
  timestamp: string;
  namespace: string;
  pod: string;
  container: string;
  line: string;
}

/**
 * Real cross-namespace/cross-pod LogQL search against GET /api/log-search ->
 * lib/loki.ts's queryLoki, which proxies the real Loki instance
 * k8s/loki-log-aggregation.yaml deploys. Every field here narrows the same
 * LogQL query -- unlike /logs's per-pod dropdown, a search here can span
 * every namespace and every pod at once. The exact LogQL query sent to
 * Loki is shown back to the operator, never hidden, matching the
 * transparency /observability's PromQL panel already established.
 */
export default function LogSearchPanel() {
  const [namespace, setNamespace] = useState("");
  const [pod, setPod] = useState("");
  const [container, setContainer] = useState("");
  const [search, setSearch] = useState("");
  const [hours, setHours] = useState(1);

  const [entries, setEntries] = useState<LogEntry[] | null>(null);
  const [logql, setLogql] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastFetchedAt, setLastFetchedAt] = useState<string | null>(null);

  async function runSearch() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ hours: String(hours), limit: "200" });
      if (namespace) params.set("namespace", namespace);
      if (pod) params.set("pod", pod);
      if (container) params.set("container", container);
      if (search) params.set("search", search);

      const res = await fetch(`/api/log-search?${params.toString()}`);
      const body = await res.json();
      setLogql(body.logql ?? null);
      if (!res.ok) {
        setError(body.error ?? `HTTP ${res.status}`);
        setEntries(null);
        return;
      }
      setEntries(body.entries ?? []);
      setLastFetchedAt(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setEntries(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-5">
        <div>
          <Label htmlFor="ls-namespace" className="mb-1 block text-xs text-muted-foreground">
            Namespace
          </Label>
          <Input
            id="ls-namespace"
            placeholder="e.g. platform-console"
            value={namespace}
            onChange={(e) => setNamespace(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="ls-pod" className="mb-1 block text-xs text-muted-foreground">
            Pod (substring)
          </Label>
          <Input
            id="ls-pod"
            placeholder="e.g. gateway"
            value={pod}
            onChange={(e) => setPod(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="ls-container" className="mb-1 block text-xs text-muted-foreground">
            Container
          </Label>
          <Input
            id="ls-container"
            placeholder="e.g. console"
            value={container}
            onChange={(e) => setContainer(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="ls-search" className="mb-1 block text-xs text-muted-foreground">
            Search text
          </Label>
          <Input
            id="ls-search"
            placeholder="line contains..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runSearch();
            }}
          />
        </div>
        <div>
          <Label htmlFor="ls-hours" className="mb-1 block text-xs text-muted-foreground">
            Last N hours
          </Label>
          <Input
            id="ls-hours"
            type="number"
            min={1}
            max={168}
            value={hours}
            onChange={(e) => setHours(Number(e.target.value) || 1)}
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={runSearch} disabled={loading}>
          {loading ? "Searching..." : "Search logs"}
        </Button>
        {lastFetchedAt && (
          <span className="text-xs text-muted-foreground">last run {lastFetchedAt}</span>
        )}
      </div>

      {logql && (
        <p className="rounded-md border border-border bg-muted/40 px-3 py-2 font-mono text-xs text-muted-foreground">
          {logql}
        </p>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription className="break-all">{error}</AlertDescription>
        </Alert>
      )}

      {entries !== null && entries.length === 0 && !error && (
        <p className="text-sm text-muted-foreground">
          no matching log lines in the last {hours}h -- try widening the time range or clearing a
          filter.
        </p>
      )}

      {entries !== null && entries.length > 0 && (
        <div className="overflow-x-auto rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>time</TableHead>
                <TableHead>namespace</TableHead>
                <TableHead>pod</TableHead>
                <TableHead>container</TableHead>
                <TableHead>line</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((entry, i) => (
                <TableRow key={`${entry.timestamp}-${i}`}>
                  <TableCell className="whitespace-nowrap font-mono text-xs">
                    {new Date(entry.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell className="text-xs">{entry.namespace}</TableCell>
                  <TableCell className="whitespace-nowrap text-xs">{entry.pod}</TableCell>
                  <TableCell className="text-xs">{entry.container}</TableCell>
                  <TableCell className="max-w-xl break-all font-mono text-xs">
                    {entry.line}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
