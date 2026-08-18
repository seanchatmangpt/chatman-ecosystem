#!/usr/bin/env node
// Build-time data-fetch script for platform-status-deck.
//
// Runs REAL kubectl commands against the live kind-platform-eng-colima cluster
// and reads the REAL platform-console evidence bundle from disk. Writes a
// single timestamped JSON snapshot that the Slidev slides import statically.
//
// This is a snapshot, not a live feed: the deck displays the timestamp this
// script wrote so staleness is always visible. If kubectl or the evidence
// file are unreachable, the script records that explicitly (status: "blocked")
// instead of fabricating numbers — no Math.random(), no hardcoded fallbacks.

import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, "..", "..", "..");
const EVIDENCE_BUNDLE_PATH = join(
  REPO_ROOT,
  "platform-console",
  "evidence",
  "control-evidence-bundle.json"
);
const OUT_DIR = join(__dirname, "..", "slides", "data");
const OUT_FILE = join(OUT_DIR, "snapshot.json");

function runKubectl(args) {
  try {
    const out = execFileSync("kubectl", args, {
      encoding: "utf8",
      timeout: 15000,
    });
    return { ok: true, out };
  } catch (err) {
    return { ok: false, error: String(err.message || err) };
  }
}

function kubectlJson(args) {
  const r = runKubectl(args);
  if (!r.ok) return { ok: false, error: r.error };
  try {
    return { ok: true, data: JSON.parse(r.out) };
  } catch (err) {
    return { ok: false, error: `parse failed: ${err.message}` };
  }
}

const snapshot = {
  generated_at: new Date().toISOString(),
  source: "scripts/snapshot-data.mjs (real kubectl + real evidence bundle read at build time)",
};

// --- kubectl context ---
const ctxResult = runKubectl(["config", "current-context"]);
snapshot.kube_context = ctxResult.ok ? ctxResult.out.trim() : null;

// --- nodes ---
const nodesResult = kubectlJson(["get", "nodes", "-o", "json"]);
if (nodesResult.ok) {
  const items = nodesResult.data.items || [];
  snapshot.cluster = {
    status: "live",
    node_count: items.length,
    nodes: items.map((n) => {
      const readyCond = (n.status?.conditions || []).find((c) => c.type === "Ready");
      return {
        name: n.metadata.name,
        ready: readyCond ? readyCond.status === "True" : null,
        kubelet_version: n.status?.nodeInfo?.kubeletVersion || null,
        creation_timestamp: n.metadata.creationTimestamp,
      };
    }),
  };
} else {
  snapshot.cluster = { status: "blocked", error: nodesResult.error };
}

// --- namespaces ---
const nsResult = kubectlJson(["get", "namespaces", "-o", "json"]);
const namespaceNames = nsResult.ok
  ? (nsResult.data.items || []).map((n) => n.metadata.name).sort()
  : [];
snapshot.namespaces = nsResult.ok
  ? { status: "live", count: namespaceNames.length, names: namespaceNames }
  : { status: "blocked", error: nsResult.error };

// --- pods (all namespaces) ---
const podsResult = kubectlJson(["get", "pods", "-A", "-o", "json"]);
if (podsResult.ok) {
  const items = podsResult.data.items || [];
  const byNamespace = {};
  for (const pod of items) {
    const ns = pod.metadata.namespace;
    if (!byNamespace[ns]) {
      byNamespace[ns] = { total: 0, running: 0, pending: 0, failed: 0, succeeded: 0, other: 0 };
    }
    byNamespace[ns].total += 1;
    const phase = pod.status?.phase || "Unknown";
    if (phase === "Running") byNamespace[ns].running += 1;
    else if (phase === "Pending") byNamespace[ns].pending += 1;
    else if (phase === "Failed") byNamespace[ns].failed += 1;
    else if (phase === "Succeeded") byNamespace[ns].succeeded += 1;
    else byNamespace[ns].other += 1;
  }
  snapshot.pods = {
    status: "live",
    total: items.length,
    by_namespace: Object.fromEntries(
      Object.entries(byNamespace).sort(([a], [b]) => a.localeCompare(b))
    ),
  };
} else {
  snapshot.pods = { status: "blocked", error: podsResult.error };
}

// --- evidence bundle (real file on disk, platform-console, read-only) ---
if (existsSync(EVIDENCE_BUNDLE_PATH)) {
  try {
    const raw = readFileSync(EVIDENCE_BUNDLE_PATH, "utf8");
    const bundle = JSON.parse(raw);
    snapshot.evidence_bundle = {
      status: "live",
      path: "platform-console/evidence/control-evidence-bundle.json",
      schema: bundle.schema || null,
      control_count: Array.isArray(bundle.controls) ? bundle.controls.length : null,
      gap_count: Array.isArray(bundle.gaps) ? bundle.gaps.length : null,
      digest: bundle.digest || null,
      bundle_generated_at: bundle.generated_at || null,
    };
  } catch (err) {
    snapshot.evidence_bundle = { status: "blocked", error: String(err.message || err) };
  }
} else {
  snapshot.evidence_bundle = { status: "blocked", error: "file not found at " + EVIDENCE_BUNDLE_PATH };
}

if (!existsSync(OUT_DIR)) mkdirSync(OUT_DIR, { recursive: true });
writeFileSync(OUT_FILE, JSON.stringify(snapshot, null, 2) + "\n");

console.log(`[snapshot-data] wrote ${OUT_FILE}`);
console.log(JSON.stringify(snapshot, null, 2));
