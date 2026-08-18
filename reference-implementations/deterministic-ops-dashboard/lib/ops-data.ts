/**
 * Deterministic, hand-fixed operational data.
 *
 * Nothing in this module is randomized or time-derived — every id, coordinate,
 * timestamp, and metric below is a literal so the page renders byte-identical
 * output on every build and every request. That determinism is the point of
 * this reference implementation: no client/server hydration drift, no
 * snapshot-test flakiness, no "works on my machine" from a clock skew.
 */

export type NodeStatus = "good" | "warning" | "critical";

export interface OpsNode {
  id: string;
  name: string;
  region: string;
  longitude: number;
  latitude: number;
  status: NodeStatus;
  cpuPct: number;
  memPct: number;
}

export interface OpsJob {
  id: string;
  name: string;
  nodeId: string;
  status: "succeeded" | "running" | "failed" | "queued";
  startedAt: string;
  durationMs: number;
  retries: number;
  throughput: number; // 0..1, used as sequential encoding weight for flow arcs
}

export interface OpsFlow {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  throughput: number; // 0..1
}

export interface OpsIncident {
  id: string;
  severity: "warning" | "critical";
  title: string;
  detail: string;
  occurredAt: string;
}

export const NODES: OpsNode[] = [
  { id: "n-use1", name: "use1-a", region: "us-east-1", longitude: -77.4874, latitude: 39.0438, status: "good", cpuPct: 41, memPct: 58 },
  { id: "n-usw2", name: "usw2-a", region: "us-west-2", longitude: -119.2684, latitude: 45.8399, status: "good", cpuPct: 37, memPct: 49 },
  { id: "n-euw1", name: "euw1-a", region: "eu-west-1", longitude: -6.2603, latitude: 53.3498, status: "warning", cpuPct: 76, memPct: 81 },
  { id: "n-apse1", name: "apse1-a", region: "ap-southeast-1", longitude: 103.8198, latitude: 1.3521, status: "good", cpuPct: 29, memPct: 44 },
  { id: "n-apne1", name: "apne1-a", region: "ap-northeast-1", longitude: 139.6917, latitude: 35.6895, status: "critical", cpuPct: 94, memPct: 88 },
  { id: "n-sae1", name: "sae1-a", region: "sa-east-1", longitude: -46.6333, latitude: -23.5505, status: "good", cpuPct: 33, memPct: 52 },
];

export const JOBS: OpsJob[] = [
  { id: "job-2201", name: "reconcile-ledger", nodeId: "n-use1", status: "succeeded", startedAt: "2026-08-17T09:02:11Z", durationMs: 41230, retries: 0, throughput: 0.82 },
  { id: "job-2202", name: "compact-index", nodeId: "n-usw2", status: "succeeded", startedAt: "2026-08-17T09:04:47Z", durationMs: 18990, retries: 0, throughput: 0.61 },
  { id: "job-2203", name: "replicate-snapshot", nodeId: "n-euw1", status: "running", startedAt: "2026-08-17T09:11:03Z", durationMs: 132400, retries: 2, throughput: 0.93 },
  { id: "job-2204", name: "verify-checksums", nodeId: "n-apse1", status: "succeeded", startedAt: "2026-08-17T09:07:29Z", durationMs: 9120, retries: 0, throughput: 0.35 },
  { id: "job-2205", name: "drain-queue", nodeId: "n-apne1", status: "failed", startedAt: "2026-08-17T09:09:52Z", durationMs: 5010, retries: 3, throughput: 0.71 },
  { id: "job-2206", name: "rotate-credentials", nodeId: "n-sae1", status: "queued", startedAt: "2026-08-17T09:15:00Z", durationMs: 0, retries: 0, throughput: 0.12 },
  { id: "job-2207", name: "backfill-metrics", nodeId: "n-use1", status: "running", startedAt: "2026-08-17T09:13:18Z", durationMs: 67800, retries: 1, throughput: 0.58 },
  { id: "job-2208", name: "gc-tombstones", nodeId: "n-euw1", status: "succeeded", startedAt: "2026-08-17T08:58:02Z", durationMs: 24310, retries: 0, throughput: 0.44 },
];

export const FLOWS: OpsFlow[] = [
  { id: "flow-1", fromNodeId: "n-use1", toNodeId: "n-euw1", throughput: 0.82 },
  { id: "flow-2", fromNodeId: "n-usw2", toNodeId: "n-apne1", throughput: 0.55 },
  { id: "flow-3", fromNodeId: "n-euw1", toNodeId: "n-apse1", throughput: 0.93 },
  { id: "flow-4", fromNodeId: "n-apne1", toNodeId: "n-sae1", throughput: 0.31 },
  { id: "flow-5", fromNodeId: "n-use1", toNodeId: "n-usw2", throughput: 0.67 },
];

export const INCIDENTS: OpsIncident[] = [
  {
    id: "inc-441",
    severity: "critical",
    title: "apne1-a CPU saturation",
    detail: "apne1-a has held CPU above 90% for 12 consecutive minutes; job-2205 failed 3 retries and was parked.",
    occurredAt: "2026-08-17T09:10:00Z",
  },
  {
    id: "inc-442",
    severity: "warning",
    title: "euw1-a memory pressure",
    detail: "euw1-a memory at 81% during replicate-snapshot; no action required, monitoring.",
    occurredAt: "2026-08-17T09:05:00Z",
  },
];

export function nodeById(id: string): OpsNode | undefined {
  return NODES.find((n) => n.id === id);
}

export const STATS = {
  totalNodes: NODES.length,
  jobsRunning: JOBS.filter((j) => j.status === "running").length,
  successRatePct: Math.round(
    (JOBS.filter((j) => j.status === "succeeded").length /
      JOBS.filter((j) => j.status !== "queued" && j.status !== "running").length) *
      1000,
  ) / 10,
  meanLatencyMs: Math.round(
    JOBS.filter((j) => j.durationMs > 0).reduce((sum, j) => sum + j.durationMs, 0) /
      JOBS.filter((j) => j.durationMs > 0).length,
  ),
};
