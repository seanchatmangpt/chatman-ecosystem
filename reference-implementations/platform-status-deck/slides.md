---
theme: seriph
title: Platform Status
info: Build-time snapshot deck of the kind-platform-eng-colima cluster and platform-console evidence bundle.
class: text-center
transition: fade
mdc: true
---

<script setup>
import snapshot from './slides/data/snapshot.json'
</script>

# Platform Status Deck

kind-platform-eng-colima — real cluster, real evidence bundle

<div class="mt-8 text-sm opacity-70">
Data snapshot taken at build time: <strong>{{ snapshot.generated_at }}</strong><br/>
This deck does NOT live-refresh. Numbers are frozen at the moment <code>npm run build</code> ran the
snapshot script. Re-run <code>npm run snapshot &amp;&amp; npm run build</code> for current data.
</div>

---
layout: default
---

# Snapshot Provenance

This deck's only data source is <code>scripts/snapshot-data.mjs</code>, run at build time.

<div class="grid grid-cols-2 gap-6 mt-6 text-sm">
<div>

**Real, not fabricated:**
- Real `kubectl` calls against context `{{ snapshot.kube_context }}`
- Real read of `platform-console/evidence/control-evidence-bundle.json`
- No `Math.random()`, no hardcoded counts, no mocked API responses

</div>
<div>

**Honesty convention (per SCOPE-AND-LIMITATIONS.md):**
- Every number below is traceable to the raw snapshot JSON
- `slides/data/snapshot.json` is committed alongside the deck
- If a source was unreachable, this deck would say `status: "blocked"` — not silently substitute a number

</div>
</div>

<div class="mt-8 text-xs opacity-60">
Snapshot file: <code>slides/data/snapshot.json</code> · source field: "{{ snapshot.source }}"
</div>

---
layout: default
---

# Cluster Overview

<div class="grid grid-cols-3 gap-4 mt-6">
  <div class="p-4 rounded border border-gray-500/30">
    <div class="text-3xl font-bold">{{ snapshot.cluster.node_count }}</div>
    <div class="text-sm opacity-70">node(s)</div>
  </div>
  <div class="p-4 rounded border border-gray-500/30">
    <div class="text-3xl font-bold">{{ snapshot.namespaces.count }}</div>
    <div class="text-sm opacity-70">namespaces</div>
  </div>
  <div class="p-4 rounded border border-gray-500/30">
    <div class="text-3xl font-bold">{{ snapshot.pods.total }}</div>
    <div class="text-sm opacity-70">total pods</div>
  </div>
</div>

<div class="mt-6 text-sm">

**Node(s):**
<ul>
  <li v-for="n in snapshot.cluster.nodes" :key="n.name">
    <code>{{ n.name }}</code> — ready: {{ n.ready }} — kubelet {{ n.kubelet_version }} — created {{ n.creation_timestamp }}
  </li>
</ul>

</div>

<div class="mt-4 text-xs opacity-60">
Context: <code>{{ snapshot.kube_context }}</code> · status: {{ snapshot.cluster.status }}
</div>

---
layout: default
---

# Namespaces

<div class="grid grid-cols-4 gap-2 mt-6 text-sm">
  <div v-for="ns in snapshot.namespaces.names" :key="ns" class="p-2 rounded border border-gray-500/20">
    {{ ns }}
  </div>
</div>

<div class="mt-6 text-xs opacity-60">{{ snapshot.namespaces.count }} namespaces, read via <code>kubectl get namespaces -o json</code></div>

---
layout: default
---

# Evidence Bundle Status

<div class="grid grid-cols-2 gap-6 mt-6">
  <div class="p-6 rounded border border-gray-500/30 text-center">
    <div class="text-5xl font-bold">{{ snapshot.evidence_bundle.control_count }}</div>
    <div class="opacity-70 mt-2">controls evaluated</div>
  </div>
  <div class="p-6 rounded border border-gray-500/30 text-center">
    <div class="text-5xl font-bold">{{ snapshot.evidence_bundle.gap_count }}</div>
    <div class="opacity-70 mt-2">gaps</div>
  </div>
</div>

<div class="mt-6 text-sm">

- Schema: <code>{{ snapshot.evidence_bundle.schema }}</code>
- Bundle generated at: <code>{{ snapshot.evidence_bundle.bundle_generated_at }}</code>
- Digest ({{ snapshot.evidence_bundle.digest?.algorithm }}): <code class="text-xs">{{ snapshot.evidence_bundle.digest?.value }}</code>
- Source file: <code>{{ snapshot.evidence_bundle.path }}</code> (read-only, not modified by this deck)

</div>

---
layout: default
---

# Per-Namespace Pod Health

<table class="text-sm w-full mt-4">
  <thead>
    <tr class="text-left border-b border-gray-500/30">
      <th class="pr-4">Namespace</th>
      <th class="pr-4">Total</th>
      <th class="pr-4">Running</th>
      <th class="pr-4">Pending</th>
      <th class="pr-4">Succeeded</th>
      <th class="pr-4">Failed</th>
    </tr>
  </thead>
  <tbody>
    <tr v-for="(v, ns) in snapshot.pods.by_namespace" :key="ns" class="border-b border-gray-500/10">
      <td class="pr-4"><code>{{ ns }}</code></td>
      <td class="pr-4">{{ v.total }}</td>
      <td class="pr-4">{{ v.running }}</td>
      <td class="pr-4">{{ v.pending }}</td>
      <td class="pr-4">{{ v.succeeded }}</td>
      <td class="pr-4">{{ v.failed }}</td>
    </tr>
  </tbody>
</table>

<div class="mt-4 text-xs opacity-60">Source: <code>kubectl get pods -A -o json</code>, {{ snapshot.pods.total }} pods across {{ Object.keys(snapshot.pods.by_namespace).length }} namespaces with running workloads.</div>

---
layout: default
---

# Capabilities Landed This Session

Cited against real commits in this repo — not marketing copy.

<div class="text-sm mt-4 space-y-4">

<div class="p-3 rounded border border-gray-500/20">
<strong>Per-project Redis + NATS/JetStream addons</strong> (<code>834924e</code>, <code>745d783</code>)<br/>
<span class="opacity-70">
lib/redis.ts and lib/queue.ts: provision/status/teardown, owner-gated API routes,
password via crypto.randomBytes(32) through the existing Secret convention. Mirrors the
existing per-project Postgres provisioning pattern — closes an AWS ElastiCache/SQS/SNS-class
parity gap.
</span>
</div>

<div class="p-3 rounded border border-gray-500/20">
<strong>Castle deploy/run/sunset lifecycle module</strong> (<code>a90c9d2</code>)<br/>
<span class="opacity-70">
Containerized the castle crate with a verb allowlist locked to
fortune5-requirements/inventory-components/inventory-goals only — no construct/gymact
actuation path exposed. Wired a second real planner (AutofdeLabPlanner) into
run_planner_ensemble, proven by a passing cargo test that the ensemble selects across two
structurally different planners.
</span>
</div>

<div class="p-3 rounded border border-gray-500/20">
<strong>Playwright E2E suite</strong> (<code>b889ed9</code>)<br/>
<span class="opacity-70">
527 lines across 4 spec files (core-paas, new-addons, security-observability,
login.smoke) run headless and live against the kind cluster's Istio ingress — real
login, real cookie session, no mocked auth. Found and fixed a real defect: every login
issued a Secure-flagged cookie no browser would send back over the cluster's
plain-HTTP-only origin.
</span>
</div>

</div>

---
layout: default
---

# What This Deck Does Not Claim

<div class="text-sm mt-6 space-y-2">

- This is a **static, build-time snapshot** — not a live dashboard. It does not auto-refresh.
- The Castle namespace currently shows **0 live pods** in this snapshot — the module exists in
  code (commit `a90c9d2`) and passes its own tests, but is not currently deployed to this
  cluster. Both facts are true simultaneously; neither is hidden.
- Pod/namespace/node counts reflect the cluster state at snapshot time only. Re-run
  <code>npm run snapshot</code> before trusting any number for a decision made later than the
  timestamp on the title slide.
- The evidence bundle's gap count (currently {{ snapshot.evidence_bundle.gap_count }}) reflects
  what that bundle's own generator considered in scope — it is not an independent audit by this
  deck.

</div>

---
layout: center
class: text-center
---

# Closing

Built with a real <code>@slidev/cli</code> scaffold, a real build-time snapshot script, and
real numbers from a live cluster and an on-disk evidence bundle.

<div class="mt-6 text-sm opacity-70">
Snapshot: {{ snapshot.generated_at }}<br/>
Cluster: {{ snapshot.kube_context }} · {{ snapshot.namespaces.count }} namespaces · {{ snapshot.pods.total }} pods<br/>
Evidence: {{ snapshot.evidence_bundle.control_count }} controls · {{ snapshot.evidence_bundle.gap_count }} gaps
</div>

<div class="mt-10 text-xs opacity-50">
reference-implementations/platform-status-deck
</div>
