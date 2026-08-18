# Sony-Readiness Gap Closure

Last updated: 2026-08-18

This document is the honest counterpart to the survey that identified 14 gaps against a
"Sony-level media company" bar across IaaS/PaaS/SaaS layers of `platform-console`. Five of
those 14 were attempted this pass (the `top5` the survey ranked highest-priority). Each is
reported below with what was actually built and the real verification evidence pulled from the
build result -- kubectl output, `tsc` status, evidence-bundle diffs. Where a build result itself
disclosed something incomplete, blocked, or unverified, that disclosure is carried through here
verbatim rather than smoothed over. The remaining 9 gaps were not touched this pass and are
listed verbatim in "Still Open" at the end.

Following this repo's own convention (`docs/SCOPE-AND-LIMITATIONS.md`): nothing here is labeled
"Sony-level" or "production-ready" as a blanket claim. Each item states the precise mechanism
that is now real, and the precise scope it does not cover.

---

## 1. IaaS -- Secrets-at-rest encryption (envelope/KMS) for k8s Secrets

**What was built**: `infra/enable-etcd-encryption.sh` generates a real AES key
(`openssl rand -base64 32`), writes an `EncryptionConfiguration` (`aescbc` provider) to
`/etc/kubernetes/pki/encryption/encryption-config.yaml` on the live control-plane container,
patches the static `kube-apiserver.yaml` manifest to add `--encryption-provider-config`, and
re-writes every existing Secret through the API so pre-existing plaintext-identity objects
become real ciphertext. `infra/verify-etcd-encryption.sh` dumps raw etcd bytes for a Secret via
`etcdctl` and scripts a check that no plaintext key/value appears in them. New control
`secrets-encrypted-at-rest-in-etcd` added to `evidence/control-evidence-bundle.json`.

**Real verification**:
- kube-apiserver restarted cleanly after the manifest patch (`Pending` → `Running`);
  `kubectl get nodes` stayed `Ready` throughout.
- All 23 live Secrets across every namespace re-encrypted (`kubectl replace` → 23 `replaced`,
  zero errors).
- Raw etcd dump of `platform-console-secrets`: literal envelope prefix
  `k8s:enc:aescbc:v1:key1:` followed by opaque binary, not base64-decodable JSON.
- Scripted cross-check: `envelope prefix present: True`, `plaintext leaks found: none`,
  `RESULT: CIPHERTEXT CONFIRMED` -- confirmed real key names (`ADMIN_PASSWORD_HASH`,
  `AUTH_SECRET`, `OIDC_CLIENT_SECRET`) and real values (including the bcrypt `$2a$` prefix) are
  absent from the raw etcd bytes.
- Digest method reproduced against the prior stored digest before editing, then the new digest
  (`cf9f9788...`) round-trip-verified.

**Disclosed scope, not laundered as full coverage**: native `aescbc` provider, not a remote
KMS or sealed-secrets controller -- the kind single-node cluster has no external KMS to
integrate with. The key lives on the same node's disk as etcd, so this defends against
etcd-data-exfiltration, backup theft, and casual inspection -- **not** against full node
compromise (an attacker with root on the node can read the key file next to the ciphertext).
Scoped to the `secrets` resource only, ConfigMaps are still plaintext.

**tsc**: pre-existing errors in `lib/audit-db.ts` and storage-signed-URL wiring exist from
other, separately in-flight uncommitted work confirmed via `git stash` to predate this change;
this build touched no `.ts`/`.tsx` file, only the two new shell scripts and the evidence JSON.

---

## 2. PaaS -- Vulnerability scan as a hard admission gate, not a one-off run

**What was built**: `app/lib/vuln-scan.ts` gained `syncVulnDenylist()`, which derives a CEL
regex alternation of every image with an unresolved CRITICAL finding and writes it to a new
ConfigMap `platform-console-vuln-denylist`. `app/app/api/security-scan/route.ts` calls it once
a scan completes. `k8s/admission-policy.yaml` adds a new `ValidatingAdmissionPolicy`
(`platform-deployments-block-critical-cves`) that reads that ConfigMap live and blocks any
Deployment referencing a denylisted image, on the same 5 platform namespaces the existing
resource-quota VAP already covers. `k8s/paas-rbac.yaml` extends the scan Role with scoped
get/patch/create rights on that one ConfigMap. New control
`vuln-scan-critical-admission-gate` added.

**Real verification** (live cluster, `kind-platform-eng-colima`):
- Both RBAC and VAP objects applied and confirmed live (`configured`/`created`).
- Live negative test via real `kubectl --dry-run=server`:
  1. Before any denylist exists, a Deployment referencing `node:10-slim` (real EOL image, 9 real
     CRITICAL CVEs) is **allowed** -- disclosed bootstrap trade-off
     (`parameterNotFoundAction: Allow`) so the gate doesn't lock out the platform before any
     scan has run.
  2. With a real denylist ConfigMap (`^(node:10-slim)$`) in place, the same Deployment is
     **rejected** with the policy's own denial message.
  3. A clean image with the same denylist active is still **admitted** (scoped block, not a
     namespace lockout).
  4. Denylist patched to the never-match sentinel → the previously-rejected image is
     **re-admitted** (remediation self-clears the block, not a one-way ratchet).
  5. No test Deployment or manually-created ConfigMap left behind.

**Disclosed gaps, not laundered**: the full UI path (real trivy scan → `POST`/`GET`
`/api/security-scan` → `syncVulnDenylist`) was **not re-exercised end-to-end through the running
app** this pass -- it would have required rotating `ADMIN_PASSWORD_HASH`, out of scope for this
task. The admission-gate mechanism itself (the exact schema/pattern format `syncVulnDenylist`
writes) was instead verified directly against the live apiserver, which is a narrower claim than
"proven end to end." `tsc --noEmit` on the full tree has one pre-existing error in
`app/app/api/audit/verify/route.ts` from separate in-flight work; filtered to files this control
touched, zero errors.

---

## 3. IaaS -- PodSecurity admission enforcement (restricted profile) on tenant namespaces

**What was built**: `k8s/namespaces.yaml` gained
`pod-security.kubernetes.io/enforce: restricted` on `autofde-lab`, `gymact`, `ggen`,
`ggen-marketplace`, and a new `supabase-demo` Namespace block carrying the same label.
`platform-console` (control plane, not tenant surface) left unlabeled. New control
`pod-security-admission-enforced` added.

**Real verification** (live cluster, k8s v1.34.0):
- `kubectl get ns ... -o custom-columns=...ENFORCE` confirms the label live on all 5 namespaces,
  absent on `platform-console`.
- Negative test: a real privileged Pod applied to `autofde-lab` is rejected with the real
  PodSecurity admission error (`privileged`, `allowPrivilegeEscalation != false`, unrestricted
  capabilities); `kubectl get pod` afterward confirms `NotFound`.
- Positive control: a fully restricted-compliant Pod is admitted (`Pending` then deleted,
  confirmed `NotFound` afterward).
- Existing workloads unaffected: `kubectl apply` emitted the expected warning that pre-existing
  pods in `supabase-demo` violate the new enforce level (PSA gates *creation*, not running
  pods), and `kubectl get pods -n supabase-demo` immediately after showed all pre-existing pods
  still `Running`/`Completed`, zero evictions.
- `npx tsc --noEmit`: clean.
- Digest round-trip confirmed (`7f7d8f75...`).

**Disclosed scope**: this is admission-time enforcement on new/updated Pods in 5 named
namespaces. It does not retroactively evict or remediate any pod already running out of
compliance in those namespaces at the time the label was applied.

---

## 4. SaaS -- Tamper-evident, isolated audit log store

**What was built**: `app/lib/audit-db.ts` added `prev_hash`/`row_hash` columns to
`platform_console.audit_log`, chained via SHA-256 (`row_hash = sha256(prev_hash + requestId +
ts + actor + method + path + status)`), writes serialized under a `pg_advisory_xact_lock` to
prevent concurrent-writer races on the chain tail, plus a one-time backfill for pre-existing
rows and a `verifyAuditChain()` that re-derives the whole chain and reports the first broken
row. New owner-gated `GET /api/audit/verify` route and a "Verify chain integrity" button in
`AuditLogPanel.tsx`. New control `audit-log-tamper-evident-hash-chain` added.

**This is the hash-chain alternative the survey gap explicitly named, not the stronger
option** (isolated/separate audit sink) -- the audit log still lives in the same Postgres
cluster it audits; what changed is that a row can no longer be silently rewritten without
detection, not that the store is physically separate.

**Real verification**:
- `npx tsc --noEmit` clean; `npm run build` succeeded with the new route present.
- Real `ALTER TABLE` confirmed live via `kubectl exec` into `demo-db-postgres-0`: `\d
  platform_console.audit_log` shows the new columns.
- **Real tamper-detection demo against the live table**: chain verified through row 200 →
  `valid:true`. A real `UPDATE ... SET status=204 WHERE id=200` executed directly via
  `kubectl exec`+`psql` (the actual attacker-with-DB-access scenario) → re-verify returned
  `valid:false, brokenAt:{id:200}`. Row restored → re-verify returned `valid:true` again.
- Evidence bundle digest reproduced against the prior stored value before editing, then the new
  digest round-trip-confirmed (60 controls total, last is this one).

**Disclosed complication**: a separate, concurrently-running session was actively editing this
same working tree and redeploying the same gateway Deployment during this pass, overwriting
`audit-db.ts` and the evidence bundle twice, including one literal NUL-byte corruption in
`audit-db.ts` that was found and fixed (re-verified `tsc` clean, zero NUL bytes). Because the
live Deployment's image tag was a moving target during this session, the **HTTP-level**
`/api/audit/verify` proof was inconsistent -- the control was instead corroborated with direct
`psql`/`kubectl exec` evidence against the live table, independent of which image happened to be
rolled out at the time. This is a narrower proof than "verified end-to-end through the running
app," and is stated as such.

---

## 5. SaaS -- Content/IP protection primitives (signed, expiring asset URLs)

**What was built**: `app/lib/storage-signed-url.ts` mints/verifies HMAC-SHA256 signed tokens
(reusing the `AUTH_SECRET` `lib/session.ts` already signs session JWTs with), TTL server-clamped
to [30s, 24h], constant-time verification, server-checked expiry. New
`GET`/`POST /api/projects/[name]/storage` (list buckets / mint signed URL, member+ role) and
`GET /api/projects/[name]/storage/download` (verify token, proxy real object bytes, audit-log
every access). `middleware.ts` gained a narrow regex exemption for the download route so the
bearer-style signed link works without a session cookie, matching real presigned-URL semantics.
New `StorageSignedUrlPanel.tsx` UI. New control `storage-signed-url-expiry-enforced` added.

**Real verification**:
- `npx tsc --noEmit` clean. Built in an isolated git worktree (seeded from repo HEAD + only this
  control's files) because the shared working tree had unrelated concurrent edits at build time
  -- `npm run build` succeeded there with the new routes present.
- Real docker build, `kind load docker-image`, `kubectl set image`/`rollout restart`,
  `kubectl rollout status` → "successfully rolled out".
- Live HTTP proof against the deployed pod: real admin login (temp-rotated password, restored
  after), a real bucket+object created against the live `demo-project` Storage API,
  `POST /api/projects/demo-project/storage` → real `201` with signed URL. Valid link → real
  **200** with the real object bytes. A second link, allowed to pass its `expiresAt` → real
  **403** `{"error":"signed URL rejected: expired"}`.
- Both accesses cross-confirmed in `GET /api/audit` (id 257 status 200, id 264 status 403).
- Test bucket/object deleted, password hash restored (confirmed via a real subsequent `401` on
  the temp password), deployment rolled back to the image the concurrent audit-chain task
  already had deployed.
- Evidence-bundle digest round-trip confirmed both directions.

**Disclosed scope**: signed-URL expiry and per-access audit logging are real and
live-verified; no watermarking or DRM is implemented (the survey gap named both, only the
signed/expiring-URL half was built this pass).

---

## Cross-cutting notes from the build results

- None of the five changes were committed or pushed -- all are staged in the working tree for
  review, per every build result.
- `app/app/castle/` and all castle-related files were explicitly confirmed untouched by every
  build result that mentioned it -- a separate in-flight task was working in that area
  concurrently and was left alone throughout.
- Multiple build results independently reported the same shared working tree had other
  concurrent, uncoordinated edits happening during this pass (vuln-scan, audit-db, k8s policy
  files, storage). Two results (items 4 and 5 above) had to route around a moving deployed
  image tag to get a verification signal that didn't depend on which concurrent edit happened to
  be live at the moment of testing.

---

## Still Open (not attempted this pass)

Verbatim from the survey, every entry not in `top5`:

### IaaS
- Single control-plane node with no HA/failover (explicitly documented in
  docs/SCOPE-AND-LIMITATIONS.md #1) -- one etcd, one API server, one kubelet; already suffered
  one unrecoverable etcd bbolt corruption requiring full manual recreation.
- No real multi-region/multi-AZ network partition tolerance -- Pod/Service CIDR both live
  inside one physical host's kernel network namespace (SCOPE-AND-LIMITATIONS.md #2).
- No customer-facing SLA -- /status reports real measured uptime but carries no contractual
  commitment, credits, or remedy (SCOPE-AND-LIMITATIONS.md #4).

### PaaS
- Database layer is single-Pod Postgres per project, no streaming replica/standby, only
  on-demand pg_dump snapshots -- no continuous point-in-time recovery
  (SCOPE-AND-LIMITATIONS.md #3); README also discloses a real observed restore defect (FK-order
  dependent rows can land unrestored).

### SaaS
- No multi-tenant billing/metering enforcement tied to hard resource caps beyond ResourceQuota
  per namespace -- 'usage-billing-math-verified-real' control computes cost math but no
  evidence of billing-triggered throttling/suspension.
- No SOC2/compliance attestation path beyond the explicit self-disclaimer that
  control-evidence-bundle.json 'is NOT a SOC 2 report... NOT an auditor's opinion' -- no mapping
  to SOC2 Trust Services Criteria, ISO 27001, or NIST CSF controls despite
  ggen-marketplace/packs/soc2-audit-pack existing as a reference doctrine.
- No incident-response automation/runbook beyond the single documented DR narrative
  (docs/DISASTER-RECOVERY.md) -- no paging/on-call integration, no automated failover, no tested
  tabletop exercise for a security breach (as opposed to infra crash) scenario.

Note: the survey's `paas_gaps` also listed the vulnerability-scanning item (closed above as
part of `top5`) and the audit-log-isolation item (partially closed above via hash-chaining,
not physical isolation) -- both are addressed in items 2 and 4 rather than repeated here.
