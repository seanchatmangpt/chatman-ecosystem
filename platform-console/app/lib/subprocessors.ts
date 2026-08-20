/**
 * Real, maker-checker-gated Sub-processor Registry -- the compliance-
 * artifact gap upstream of lib/dpa-records.ts (which proves a DPA was
 * SIGNED) and lib/data-residency-attestation.ts (which proves a REGION
 * PINNING actually held): neither one tells a Fortune-5 legal/procurement
 * team WHO ELSE (which cloud regions, which third-party services already
 * declared in lib/data-residency-attestation.ts's own region-pinning
 * story) this platform hands their personal data to -- the GDPR Art. 28(2)
 * "list of sub-processors" every real enterprise DPA's own Schedule
 * requires, and the Art. 28(2) "authorise... any intended changes...
 * giving the controller the opportunity to object" obligation that
 * requires every affected org to actually be TOLD when that list changes,
 * not just be able to look it up on request.
 *
 * Storage: one real k8s ConfigMap (`platform-console-subprocessors`,
 * `platform-console` namespace), the exact get-then-create-or-patch
 * getConfigMap/createOrUpdateConfigMap primitive lib/dpa-records.ts's
 * header comment documents lib/dsar.ts/lib/orgs.ts/lib/authz.ts already
 * use -- no new k8s resource kind, no new RBAC verb. Key shape: one key
 * per sub-processor id (kebab-case, already ConfigMap-key-safe), value an
 * APPEND-ONLY JSON array of SubprocessorChangeEvent -- the exact same
 * append-only-array-in-one-ConfigMap-value pattern lib/dpa-records.ts
 * itself uses for its own per-org record history, and lib/audit-db.ts's
 * header comment documents for its hash-chain segments: a sub-processor
 * being added, updated, or removed is always visible history, never a
 * silent overwrite -- exactly the audit trail a DPA Schedule needs to be
 * able to show "as of date X, sub-processor Y was added/removed."
 *
 * Maker-checker: every mutation (add/update/remove) goes through the
 * exact same lib/approval-workflow.ts `requireApproval` gate
 * `pricing.override`/`sso.role-mapping.update` already use -- adding or
 * removing WHO processes every customer's personal data is exactly the
 * "can quietly widen or narrow a real compliance/security posture on an
 * ongoing basis" class of risk those two actions already earn this bar
 * for. One owner's own say-so is never sufficient; a second, distinct
 * owner-role approver must sign off before the registry ever changes.
 *
 * Change-notification: `applySubprocessorChange` (called only after a
 * fresh approval exists, same "bind exactly what was approved" discipline
 * PUT /api/orgs/[id]/pricing-override already establishes) appends the
 * change event, then emails every real org (lib/orgs.ts's `listOrgs`)
 * whose `ownerIdentifier` is a plausible email address
 * (lib/email.ts's `isPlausibleEmail`, the same gate
 * lib/status-subscriptions.ts's email-type subscribers already pass
 * through) via lib/email.ts's real SMTP client -- same "email has no
 * retry/backoff pipeline; a send failure is logged and not retried,
 * disclosed here rather than silently implied to have webhook-grade
 * durability" discipline lib/status-subscriptions.ts's header comment
 * already establishes for its own email-type delivery. A send failure
 * never blocks or reverts the already-durably-recorded registry change.
 *
 * DPA Schedule generation: `generateDpaSubprocessorSchedule` renders the
 * platform's own CURRENT sub-processor list into the plain-text Schedule
 * document format an enterprise legal team's own DPA template expects to
 * attach verbatim -- computed live from this registry's own current
 * state, never a hand-maintained document that can drift from what this
 * console actually shows a customer via the registry API.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";
import { isPlausibleEmail, sendEmail } from "@/lib/email";
import { listOrgs } from "@/lib/orgs";

export const SUBPROCESSORS_NAMESPACE = "platform-console";
export const SUBPROCESSORS_CONFIGMAP = "platform-console-subprocessors";

export type SubprocessorCategory = "cloud-infrastructure" | "third-party-service";

/**
 * The non-secret shape of one sub-processor -- cross-references the same
 * region vocabulary lib/data-residency-attestation.ts's own
 * `topology.kubernetes.io/region` labels and lib/orgs.ts's `setOrgRegion`
 * already use for `regions`, so a legal reviewer sees the exact same
 * region identifiers this console's own residency-attestation evidence
 * is expressed in, never a second, divergent naming scheme.
 */
export interface SubprocessorRecord {
  id: string;
  name: string;
  category: SubprocessorCategory;
  /** Real region identifiers (e.g. "us-east-1"), the same vocabulary
   * lib/data-residency-attestation.ts's region labels use. */
  regions: string[];
  /** What this sub-processor is used for (e.g. "primary compute/storage
   * infrastructure", "outbound transactional email delivery"). */
  purpose: string;
  /** Categories of personal data this sub-processor may process (e.g.
   * "account identifiers", "billing contact details") -- the exact list
   * an enterprise DPA's Schedule itemizes per sub-processor. */
  dataCategories: string[];
}

export type SubprocessorChangeAction = "added" | "updated" | "removed";

/** One real, immutable change event -- the unit this module's ConfigMap
 * value append-only-array actually stores, one per (sub-processor,
 * mutation). `record` is the FULL post-change snapshot (not a diff), so a
 * later reviewer can reconstruct the Schedule as it stood at any point in
 * history by replaying events up to a cutoff, without needing a separate
 * diffing step. */
export interface SubprocessorChangeEvent {
  action: SubprocessorChangeAction;
  record: SubprocessorRecord;
  changedByIdentifier: string;
  changedAt: string;
}

export interface SubprocessorCurrent {
  id: string;
  record: SubprocessorRecord | null;
  /** "removed" once the most recent event for this id is a "removed"
   * event -- absent from the active Schedule but still queryable here as
   * real history, same "history is never deleted" discipline
   * lib/dpa-records.ts's append-only design already establishes. */
  active: boolean;
  history: SubprocessorChangeEvent[];
}

function isSubprocessorRecord(value: unknown): value is SubprocessorRecord {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.name === "string" &&
    (v.category === "cloud-infrastructure" || v.category === "third-party-service") &&
    Array.isArray(v.regions) &&
    v.regions.every((r) => typeof r === "string") &&
    typeof v.purpose === "string" &&
    Array.isArray(v.dataCategories) &&
    v.dataCategories.every((d) => typeof d === "string")
  );
}

function isSubprocessorChangeEvent(value: unknown): value is SubprocessorChangeEvent {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    (v.action === "added" || v.action === "updated" || v.action === "removed") &&
    isSubprocessorRecord(v.record) &&
    typeof v.changedByIdentifier === "string" &&
    typeof v.changedAt === "string"
  );
}

function isSubprocessorChangeEventArray(value: unknown): value is SubprocessorChangeEvent[] {
  return Array.isArray(value) && value.every(isSubprocessorChangeEvent);
}

async function getAll(): Promise<K8sResult<Record<string, SubprocessorChangeEvent[]>>> {
  const existing = await getConfigMap(SUBPROCESSORS_NAMESPACE, SUBPROCESSORS_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, SubprocessorChangeEvent[]> = {};
  for (const [id, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (isSubprocessorChangeEventArray(rows)) parsed[id] = rows;
      // A hand-edited or corrupt value is skipped, not fatal -- same
      // discipline lib/dpa-records.ts's getAll uses for its own
      // ConfigMap.
    } catch {
      // ignore -- malformed JSON for this sub-processor's key
    }
  }
  return { ok: true, data: parsed };
}

function toCurrent(id: string, history: SubprocessorChangeEvent[]): SubprocessorCurrent {
  const sorted = [...history].sort((a, b) => a.changedAt.localeCompare(b.changedAt));
  const last = sorted[sorted.length - 1] ?? null;
  return {
    id,
    record: last ? last.record : null,
    active: last ? last.action !== "removed" : false,
    history: sorted,
  };
}

/** Every sub-processor this registry has ever recorded, oldest-history-
 * first per id -- backs GET /api/subprocessors's full listing (including
 * removed ones, since "we used to use X" is real, auditable history a
 * legal team may still need to see). */
export async function listSubprocessors(): Promise<K8sResult<SubprocessorCurrent[]>> {
  const all = await getAll();
  if (!all.ok) return all;
  return {
    ok: true,
    data: Object.entries(all.data)
      .map(([id, history]) => toCurrent(id, history))
      .sort((a, b) => a.id.localeCompare(b.id)),
  };
}

/** One sub-processor's full history, or `null` if this id has never had
 * an event recorded -- backs GET /api/subprocessors/[id]. */
export async function getSubprocessor(id: string): Promise<K8sResult<SubprocessorCurrent | null>> {
  const all = await getAll();
  if (!all.ok) return all;
  const history = all.data[id];
  if (!history) return { ok: true, data: null };
  return { ok: true, data: toCurrent(id, history) };
}

/** Every currently-active sub-processor (`active: true`) -- the exact
 * set `generateDpaSubprocessorSchedule` below renders into the Schedule
 * document, and the set every affected org is notified about on change. */
export async function listActiveSubprocessors(): Promise<K8sResult<SubprocessorRecord[]>> {
  const all = await listSubprocessors();
  if (!all.ok) return all;
  return {
    ok: true,
    data: all.data.filter((s) => s.active && s.record).map((s) => s.record as SubprocessorRecord),
  };
}

export type SubprocessorMutationError = "already_removed" | "not_found" | "duplicate_id";

/**
 * Appends one real change event for a sub-processor and, only once that
 * append has durably succeeded, notifies every real org via email --
 * never the reverse order, so a notification is never sent for a change
 * that failed to persist. Called ONLY after a fresh
 * `subprocessor.registry.update` approval already exists (the caller,
 * POST/PUT/DELETE /api/subprocessors[/[id]], binds exactly the approved
 * `resourcePayload.requestedSubprocessorChange`, same "bind exactly what
 * was approved" discipline PUT /api/orgs/[id]/pricing-override already
 * establishes) -- this function itself performs no approval check, same
 * separation of concerns lib/orgs.ts's setOrgPricingOverride (writer) vs.
 * the route (approval gate) already establishes.
 */
export async function applySubprocessorChange(input: {
  action: SubprocessorChangeAction;
  record: SubprocessorRecord;
  changedByIdentifier: string;
}): Promise<K8sResult<{ event: SubprocessorChangeEvent; notifiedOrgCount: number }> | { ok: false; error: SubprocessorMutationError }> {
  const all = await getAll();
  if (!all.ok) return all;

  const existingHistory = all.data[input.record.id] ?? [];
  const currentBeforeChange = toCurrent(input.record.id, existingHistory);

  if (input.action === "added" && existingHistory.length > 0 && currentBeforeChange.active) {
    return { ok: false, error: "duplicate_id" };
  }
  if ((input.action === "updated" || input.action === "removed") && !currentBeforeChange.active) {
    return { ok: false, error: currentBeforeChange.record ? "already_removed" : "not_found" };
  }

  const event: SubprocessorChangeEvent = {
    action: input.action,
    record: input.record,
    changedByIdentifier: input.changedByIdentifier,
    changedAt: new Date().toISOString(),
  };
  const updatedHistory = [...existingHistory, event];

  const writeResult = await createOrUpdateConfigMap(SUBPROCESSORS_NAMESPACE, SUBPROCESSORS_CONFIGMAP, {
    [input.record.id]: JSON.stringify(updatedHistory),
  });
  if (!writeResult.ok) return writeResult;

  const notifiedOrgCount = await notifyOrgsOfSubprocessorChange(event);
  return { ok: true, data: { event, notifiedOrgCount } };
}

/**
 * Real, best-effort email fan-out to every org's owner on a real
 * sub-processor change -- the GDPR Art. 28(2) "opportunity to object"
 * notice. Returns the count of real sends that succeeded (never a
 * fabricated "all sent" claim); a per-org send failure is neither
 * retried nor allowed to abort the fan-out to every other org, same
 * "one org's failure never blocks every other org" discipline
 * lib/data-residency-attestation.ts's platform-wide scan walker already
 * establishes. Orgs with no plausible-email `ownerIdentifier` (e.g. an
 * SSO `sub` claim rather than an email address) are silently skipped --
 * there is no other verified contact channel for them in this registry,
 * same gate lib/status-subscriptions.ts's email-type subscribers already
 * pass through before this module ever attempts SMTP.
 */
async function notifyOrgsOfSubprocessorChange(event: SubprocessorChangeEvent): Promise<number> {
  const orgsResult = await listOrgs();
  if (!orgsResult.ok) return 0;

  const verb =
    event.action === "added" ? "added to" : event.action === "removed" ? "removed from" : "updated in";
  const subject = `Sub-processor change notice: ${event.record.name}`;
  const text = [
    `This is an automated notice that a sub-processor has been ${verb} the platform's sub-processor registry.`,
    ``,
    `Sub-processor: ${event.record.name}`,
    `Category: ${event.record.category}`,
    `Regions: ${event.record.regions.join(", ") || "(none declared)"}`,
    `Purpose: ${event.record.purpose}`,
    `Data categories: ${event.record.dataCategories.join(", ") || "(none declared)"}`,
    `Effective: ${event.changedAt}`,
    ``,
    `The full, current sub-processor list is available in your DPA Schedule via the platform console.`,
  ].join("\n");

  let notified = 0;
  for (const org of orgsResult.data) {
    if (!isPlausibleEmail(org.ownerIdentifier)) continue;
    const result = await sendEmail({ to: org.ownerIdentifier, subject, text });
    if (result.ok) notified += 1;
    // A send failure is logged by lib/email.ts's own SMTP client
    // internals; it is not retried and does not abort the fan-out to
    // the remaining orgs, same discipline lib/status-subscriptions.ts's
    // header comment already discloses for its own email-type delivery.
  }
  return notified;
}

/**
 * Renders the platform's own CURRENT active sub-processor list into the
 * plain-text DPA Schedule format an enterprise legal team's own DPA
 * template expects to attach verbatim -- computed live from this
 * registry's real current state (never a hand-maintained document), so
 * the Schedule a customer downloads can never drift from what
 * GET /api/subprocessors itself shows.
 */
export async function generateDpaSubprocessorSchedule(): Promise<K8sResult<string>> {
  const activeResult = await listActiveSubprocessors();
  if (!activeResult.ok) return activeResult;

  const lines = [
    "DPA Schedule -- Authorised Sub-processors",
    `Generated: ${new Date().toISOString()}`,
    "",
    activeResult.data.length === 0
      ? "No sub-processors are currently recorded."
      : "The Controller authorises the Processor to engage the following sub-processors:",
    "",
  ];
  for (const s of activeResult.data) {
    lines.push(`- ${s.name} (${s.category})`);
    lines.push(`  Regions: ${s.regions.join(", ") || "(none declared)"}`);
    lines.push(`  Purpose: ${s.purpose}`);
    lines.push(`  Data categories: ${s.dataCategories.join(", ") || "(none declared)"}`);
    lines.push("");
  }
  return { ok: true, data: lines.join("\n") };
}
