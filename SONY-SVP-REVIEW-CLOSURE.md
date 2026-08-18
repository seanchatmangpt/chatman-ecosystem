# SVP Review Closure

Last updated: 2026-08-18

This document responds to five gaps raised in an SVP review of `platform-console`. For each,
it states the real concern as raised, what was actually built against it, and the real
verification evidence cited in the build result -- not a restatement of intent. Where a build
result reports something scoped down, incomplete, or inconsistent with the task description
(e.g. a stale control count), that is stated here plainly rather than smoothed over, matching
the disclosure discipline in `platform-console/docs/SCOPE-AND-LIMITATIONS.md`.

**None of this work is described as "Sony-ready" or "production-ready."** Every item below is a
control or a document added to a self-assessed evidence bundle that already carries its own
disclaimer: not a SOC2 report, not an auditor's opinion. All changes described here were left
**staged/uncommitted** for review, per the task's own instructions -- nothing was committed or
pushed.

---

## 1. Cost/spend dashboard

**SVP concern**: the underlying billing math and budget-alert logic were already verified real,
but only as engineering artifacts (a JSON evidence bundle, a single-fire threshold test) -- not
a page an SVP could screenshot into a QBR to show spend-by-namespace, budget-vs-actual, and a
trend, the way AWS Cost Explorer / GCP Billing / Azure Cost Management do as a first-class
screen.

**What was built**: a new `/cost` page (`app/app/cost/page.tsx`) plus a pure presentation layer
(`app/lib/cost.ts`) that joins two already-existing, already-verified data sources --
`lib/invoice-preview.ts` / `getNamespaceUsageMetrics` for current spend by namespace, and
`lib/budget-alerts.ts#listBudgetUsages` for budget status -- into one dashboard: a bar/table of
spend by namespace, share-of-total bars, a budget-vs-actual status chip, a trailing-window
trend chart (15m/1h/6h/24h Prometheus queries), and a client-side CSV export
(`app/components/CostExportButton.tsx`). No new billing math was written. A new control,
`cost-dashboard-renders-live-billing-data`, was appended to the evidence bundle.

**Verification cited in the build result**: the digest-reproduction method was confirmed before
writing (blanked `digest.value`, re-serialized, hashed with blake3, matched the prior stored
digest exactly), then re-applied to compute the new digest after the append, and re-verified to
round-trip. `npx tsc --noEmit` reported `TSC_CLEAN`. No `kubectl` evidence was collected for
this control, on the stated grounds that it's a presentation layer over data other controls
already verified live -- that is a real scope limit of this control's evidence, not a gap the
build result hides.

**Honest gap**: the trend chart is trailing-window Prometheus data (15m/1h/6h/24h), not
discrete historical billing periods -- there is no persisted billing ledger on this cluster, and
the build result states that limitation in-page rather than presenting the trend as calendar-
period billing history.

---

## 2. Data residency / region statement

**SVP concern**: no standalone, procurement-citable document states where customer/production
data physically lives -- the answer existed only by reverse-engineering a DR runbook and an
engineer-facing limitations doc.

**What was built**: `platform-console/docs/DATA-RESIDENCY.md`, a standalone statement covering
the physical chain (host machine → colima VM → single-node kind cluster) and a per-data-category
table (Postgres rows, object storage, audit logs, secrets) with the physical location of each;
an explicit statement that there is no multi-region replication, no region-selection mechanism,
and no data-locality guarantee; a disclosed gap that Kubernetes Secrets are unencrypted at
etcd's default (no KMS provider configured); and a list of what a real region guarantee would
require (multi-AZ control plane, region-pinned storage, a region-selection API, KMS, a
sub-processor list, a DPA). Cross-linked from `README.md` and `docs/SCOPE-AND-LIMITATIONS.md`.

**Verification cited in the build result**: real, live commands run this session --
`kubectl get nodes -o wide` (exactly one node, `Ready`), `kubectl get sc` (default StorageClass
`standard`, provisioner `rancher.io/local-path`, node-local disk), `kubectl get pvc -A` (all 4
project PVCs bound via that provisioner), `colima status` (VM on macOS Virtualization.Framework,
confirming single physical host). The digest method was reproduced before writing (raw-file
string substitution of the digest value, not JSON re-serialization -- confirmed as the correct
method for this particular file state) and the new digest was re-verified to round-trip.

**Honest gap**: this document makes no new engineering claim -- it restates already-verified
single-node/single-machine facts in procurement-facing language. It does not add encryption,
replication, or any residency guarantee; it discloses the absence of those.

---

## 3. Support/escalation path and on-call SLA

**SVP concern**: DISASTER-RECOVERY.md documents one past incident and technical recovery steps,
but there is no support contract, on-call policy, or escalation chain a vendor-management or
procurement team could file -- and the DR doc's own "Still Open" section already flags "no
paging/on-call integration" as unaddressed.

**What was built**: `platform-console/docs/SUPPORT-AND-ESCALATION.md` (114 lines), stating
plainly this is a **single-maintainer, best-effort support model** -- confirmed via
`git log --format='%an <%ae>' | sort -u` returning exactly one identity -- with no paging
vendor and no contractual SLA, explicitly tied to `SCOPE-AND-LIMITATIONS.md`'s existing "no
SLA" disclosure. It defines Sev1/Sev2/Sev3 tiers with platform-grounded examples (including the
real etcd-node-down scenario from `DISASTER-RECOVERY.md`), internal (non-contractual) response
targets, the real single-contact escalation chain with no backup responder, how stakeholders
currently learn of incidents (the live `/status` page plus direct contact), and a numbered list
of four gaps this document does **not** close: no paging integration, no second responder, no
incident-comms template/tracker at write time, no contractual SLA.

**Verification cited in the build result**: the `git log` single-author check was run and
returned one identity, matching the doc's claim. Digest method reproduced and matched before
writing. No TypeScript files were touched, so no `tsc` run was required for this change.

**Honest gap the build result surfaces directly**: while this task was running, the evidence
bundle's control count moved from 63 to 66 due to other concurrent, unrelated work appending
controls in parallel -- the build result explicitly notes this rather than presenting a stale
count, and re-ran the digest verification against the file's actual final on-disk state
(stored and recomputed digests both `68bf9a53...`, confirmed matching). This is a genuinely
best-effort, single-team support model today, not a placeholder understating a real on-call
rotation that exists elsewhere.

---

## 4. Incident-communication template

**SVP concern**: DISASTER-RECOVERY.md is an engineer's runbook, not something forwardable to
leadership or a customer during an active incident -- there was no pre-approved,
non-technical template, so that translation happened ad hoc each time.

**What was built**: `platform-console/docs/INCIDENT-COMMUNICATION-TEMPLATE.md`, a fill-in-the-
blank template (initial notification / ongoing-update cadence / resolution notice) for a
non-technical audience, with an explicit rule banning internal tool/component names from
external messages, cross-linked both directions with `DISASTER-RECOVERY.md`. It includes one
worked example translating the real, documented 2026-08-17 etcd-corruption incident (start
time, restand order/timing, and the honest lost-vs-recovered data split) directly from
`DISASTER-RECOVERY.md` sections 1-3 into the template's format -- with illustrative-only
placeholders (an ETA promise, an on-call contact) explicitly marked as illustrative rather than
presented as real commitments.

**Verification cited in the build result**: the doc's own "Honest scope" section states it is a
manual template, not a wired-up feature -- there is no `/incident-comms` page or API route,
matching the existing disclosure convention. Digest reproduced and confirmed before writing
(`0c889240...` matched), new digest `68bf9a53...` computed and re-verified to round-trip.

**Honest gap the build result surfaces directly**: the task description said "63 controls";
the actual file state at the time had 64 (from other concurrent work), and the build used the
real count rather than the stated one -- an explicit, stated correction, not silently absorbed.

---

## 5. SOC2/ISO control mapping

**SVP concern**: the evidence bundle's own self-disclaimer ("NOT a SOC 2 report... NOT an
auditor's opinion") is honest but leaves nothing to hand a compliance team asking which Trust
Services Criteria the platform's controls actually cover -- despite `soc2-audit-pack` existing
in the same repo family as reference doctrine for exactly this kind of mapping.

**What was built**: `platform-console/docs/SOC2-CONTROL-MAPPING.md`, mapping the evidence
bundle's controls to the AICPA Trust Services Criteria structure defined in
`ggen-marketplace/packs/soc2-audit-pack/ontology.ttl` (verified that file's
TSC-CATEGORIES/CC-CRITERIA/Availability/Confidentiality/Processing-Integrity/Privacy SKOS
schemes actually exist before citing them). 54 of 62 distinct control names were mapped to at
least one TSC category (several to more than one -- e.g. `mtls-enforced` to both Security and
Confidentiality); **7 distinct controls were explicitly marked "Not mapped"** rather than
force-fit (product/UX/dev-experience checks such as
`quickstart-script-runs-clean-end-to-end` and
`global-search-finds-real-cross-resource-matches`). The Privacy category carries **zero**
mappings, disclosed plainly as genuinely out of scope because the platform doesn't process or
hold a documented PII lifecycle -- not omitted silently. The doc carries forward the bundle's
existing disclaimer and states explicitly that no ISO 27001 or NIST CSF mapping was attempted,
because no reference doctrine for those exists in this ecosystem. `SONY-READINESS-GAP-CLOSURE.md`
was updated to strike the "no SOC2 mapping" item from its Still Open list, pointing at this doc.

**Verification cited in the build result**: digest method reproduced and confirmed matching
before writing (`0c8892...` matched stored value); new digest computed after the append and
confirmed to round-trip against the final file state. No TypeScript touched, so no `tsc` run
was applicable; JSON validity of the evidence bundle was confirmed by successful reparse.

**Honest gap**: this is a mapping exercise over controls that were already independently
verified elsewhere -- it adds no new technical control, and 7 of 62 controls plus one entire
TSC category (Privacy) are explicitly left unmapped rather than papered over.

---

## Cross-cutting notes

- **Concurrency, not sequencing**: multiple build results independently report the evidence
  bundle's control count changing out from under them mid-task (63 → 64 → 66 → recomputed
  final states) because this work ran concurrently against a shared file. Each build result
  states this explicitly and re-verified its digest against the actual final on-disk state
  rather than a stale count -- this is called out here rather than smoothed into a single
  clean number.
- **Nothing committed**: every build result confirms via `git status`/`git status --porcelain`
  that changes are staged/unstaged but not committed or pushed, per the task's own instruction.
- **No blanket readiness claim**: each item above closes one named, scoped gap. None of them,
  individually or together, constitute a certification, an SLA, or a "Sony-ready" or
  "production-ready" claim -- consistent with the disclaimers already present in
  `evidence/control-evidence-bundle.json` and `docs/SCOPE-AND-LIMITATIONS.md`.
