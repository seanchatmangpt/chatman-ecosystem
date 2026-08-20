/**
 * Denied-Party / Export-Control Screening Register -- the specific
 * procurement gate a Fortune-5 cross-border SaaS deal cannot close
 * without: every org admin, billing contact, and named technical
 * contact screened by NAME against a maintained denied-party list
 * (OFAC SDN / BIS Entity List / consolidated-list style name matching)
 * on every add or change, with a queryable per-org register of every
 * screening run and its result, timestamped, so legal/export-compliance
 * can review and sign off BEFORE the contract closes. Nothing in
 * lib/dpa-records.ts (signature record), lib/subprocessors.ts (who
 * processes data), or lib/le-requests.ts (government demands already
 * received) covers "is this named human being on a sanctions list" --
 * this module is that gap.
 *
 * Storage: two real k8s ConfigMaps, same
 * getConfigMap/createOrUpdateConfigMap get-then-create-or-patch
 * primitive lib/dpa-records.ts/lib/subprocessors.ts/lib/le-requests.ts
 * already use -- no new k8s resource kind:
 *   - `platform-denied-party-list` (this platform's own maintained name
 *     list an export-compliance admin curates -- deliberately NOT a live
 *     call to a paid third-party screening API, out of scope the same
 *     way lib/dpa-records.ts deliberately does not perform e-signing;
 *     this module screens against the REAL list this platform actually
 *     maintains, never a fabricated or hardcoded one). Single key
 *     `"entries"` -> JSON DeniedPartyListEntry[].
 *   - `platform-denied-party-screening` -- one key per org id, each
 *     value an APPEND-ONLY JSON array of ScreeningRecord, same
 *     append-only-array-in-one-ConfigMap-value discipline
 *     lib/dpa-records.ts's header comment documents (and, in turn,
 *     lib/audit-db.ts's own hash-chain segments): a new screening run is
 *     appended, nothing already written is ever mutated or removed, so
 *     the full history of every match and every override decision stays
 *     visible.
 *
 * Screening is real, deterministic, offline name matching (normalized
 * case/diacritics/punctuation-insensitive exact and substring match)
 * against the maintained list -- not a fabricated "always clear" stub.
 * A "potential_match" screening result is a REAL hard gate: the contact
 * is NOT usable (see `isOrgClearedForScreening`) until a second,
 * distinct owner-role approver reviews the match and records a
 * maker-checker override decision via the existing
 * lib/approval-workflow.ts `denied-party.override` action -- the exact
 * two-person-integrity bar `dsar.erasure`/`le-request.respond` already
 * set for irreversible-consequence, single-employee-could-hide-it
 * classes of risk. A "clear" result requires no approval.
 */
import { createOrUpdateConfigMap, getConfigMap, type K8sResult } from "@/lib/k8s";

export const DENIED_PARTY_LIST_NAMESPACE = "platform-console";
export const DENIED_PARTY_LIST_CONFIGMAP = "platform-denied-party-list";
export const DENIED_PARTY_SCREENING_NAMESPACE = "platform-console";
export const DENIED_PARTY_SCREENING_CONFIGMAP = "platform-denied-party-screening";

export type ContactRole = "org_admin" | "billing_contact" | "technical_contact";

export interface DeniedPartyListEntry {
  id: string;
  /** The denied party's full name as it appears on the source list --
   * matching is normalized (case/diacritic/punctuation-insensitive), so
   * this is stored in its original, human-readable form. */
  name: string;
  /** The maintained source this entry traces to, e.g. "OFAC SDN",
   * "BIS Entity List", "Consolidated Screening List" -- free text, this
   * module does not itself pull a live third-party feed. */
  source: string;
  /** Optional alternate spellings/aliases screened the same as `name`. */
  aliases?: string[];
  addedAt: string;
  addedByIdentifier: string;
}

export type ScreeningResult = "clear" | "potential_match";

export interface ScreeningMatch {
  listEntryId: string;
  matchedName: string;
  /** Which of `name`/an alias in the list entry actually matched. */
  matchedAgainst: string;
}

export interface ScreeningRecord {
  id: string;
  orgId: string;
  contactRole: ContactRole;
  contactName: string;
  contactEmail: string;
  result: ScreeningResult;
  matches: ScreeningMatch[];
  screenedAt: string;
  screenedByIdentifier: string;
  /**
   * Maker-checker override decision for a "potential_match" result --
   * absent until a second, distinct owner-role approver has reviewed it
   * via lib/approval-workflow.ts's `denied-party.override` action.
   * Absent entirely for every "clear" result, which requires no
   * override.
   */
  override?: {
    decision: "cleared_to_proceed" | "confirmed_blocked";
    decidedByIdentifier: string;
    decidedAt: string;
    justification: string;
  };
}

function isContactRole(value: unknown): value is ContactRole {
  return value === "org_admin" || value === "billing_contact" || value === "technical_contact";
}

function isDeniedPartyListEntry(value: unknown): value is DeniedPartyListEntry {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.name === "string" &&
    typeof v.source === "string" &&
    (v.aliases === undefined || (Array.isArray(v.aliases) && v.aliases.every((a) => typeof a === "string"))) &&
    typeof v.addedAt === "string" &&
    typeof v.addedByIdentifier === "string"
  );
}

function isScreeningMatch(value: unknown): value is ScreeningMatch {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.listEntryId === "string" &&
    typeof v.matchedName === "string" &&
    typeof v.matchedAgainst === "string"
  );
}

function isScreeningRecord(value: unknown): value is ScreeningRecord {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  if (
    typeof v.id !== "string" ||
    typeof v.orgId !== "string" ||
    !isContactRole(v.contactRole) ||
    typeof v.contactName !== "string" ||
    typeof v.contactEmail !== "string" ||
    (v.result !== "clear" && v.result !== "potential_match") ||
    !Array.isArray(v.matches) ||
    !v.matches.every(isScreeningMatch) ||
    typeof v.screenedAt !== "string" ||
    typeof v.screenedByIdentifier !== "string"
  ) {
    return false;
  }
  if (v.override !== undefined) {
    const o = v.override as Record<string, unknown>;
    if (
      typeof o !== "object" ||
      o === null ||
      (o.decision !== "cleared_to_proceed" && o.decision !== "confirmed_blocked") ||
      typeof o.decidedByIdentifier !== "string" ||
      typeof o.decidedAt !== "string" ||
      typeof o.justification !== "string"
    ) {
      return false;
    }
  }
  return true;
}

/**
 * Normalizes a name for matching: lowercased, diacritics stripped,
 * punctuation collapsed to single spaces, trimmed. Deterministic and
 * offline -- no fuzzy/ML matching, so every match this module reports is
 * exactly reproducible by a human reviewer re-running the same
 * comparison by eye.
 */
export function normalizeNameForScreening(name: string): string {
  return name
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** Real substring/exact name-match screening against one list entry --
 * matches on the entry's own `name` and every `alias`. */
function matchAgainstEntry(normalizedContactName: string, entry: DeniedPartyListEntry): ScreeningMatch | null {
  const candidates = [entry.name, ...(entry.aliases ?? [])];
  for (const candidate of candidates) {
    const normalizedCandidate = normalizeNameForScreening(candidate);
    if (!normalizedCandidate) continue;
    if (
      normalizedContactName === normalizedCandidate ||
      normalizedContactName.includes(normalizedCandidate) ||
      normalizedCandidate.includes(normalizedContactName)
    ) {
      return { listEntryId: entry.id, matchedName: entry.name, matchedAgainst: candidate };
    }
  }
  return null;
}

/** Screens one contact name against the full list, returning every
 * matching entry (never just the first) so a reviewer sees the complete
 * picture. */
export function screenNameAgainstList(
  contactName: string,
  list: DeniedPartyListEntry[],
): ScreeningMatch[] {
  const normalized = normalizeNameForScreening(contactName);
  if (!normalized) return [];
  const matches: ScreeningMatch[] = [];
  for (const entry of list) {
    const match = matchAgainstEntry(normalized, entry);
    if (match) matches.push(match);
  }
  return matches;
}

// ---- Denied-party list (maintained by export-compliance) ----

async function getListAll(): Promise<K8sResult<DeniedPartyListEntry[]>> {
  const existing = await getConfigMap(DENIED_PARTY_LIST_NAMESPACE, DENIED_PARTY_LIST_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: [] };
  const raw = existing.data.data["entries"];
  if (!raw) return { ok: true, data: [] };
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (Array.isArray(parsed) && parsed.every(isDeniedPartyListEntry)) {
      return { ok: true, data: parsed };
    }
    return { ok: true, data: [] };
  } catch {
    return { ok: true, data: [] };
  }
}

export async function listDeniedParties(): Promise<K8sResult<DeniedPartyListEntry[]>> {
  return getListAll();
}

/** Appends one new denied-party list entry -- append-only, same
 * discipline lib/dpa-records.ts's appendDpaRecord establishes: the list
 * only ever grows or is corrected by a new entry, never silently edited
 * in place. */
export async function appendDeniedPartyListEntry(
  entry: DeniedPartyListEntry,
): Promise<K8sResult<DeniedPartyListEntry[]>> {
  const all = await getListAll();
  if (!all.ok) return all;
  const updated = [...all.data, entry];
  const result = await createOrUpdateConfigMap(DENIED_PARTY_LIST_NAMESPACE, DENIED_PARTY_LIST_CONFIGMAP, {
    entries: JSON.stringify(updated),
  });
  if (!result.ok) return result;
  return { ok: true, data: updated };
}

// ---- Per-org screening register ----

async function getScreeningAll(): Promise<K8sResult<Record<string, ScreeningRecord[]>>> {
  const existing = await getConfigMap(DENIED_PARTY_SCREENING_NAMESPACE, DENIED_PARTY_SCREENING_CONFIGMAP);
  if (!existing.ok) return existing;
  if (!existing.data) return { ok: true, data: {} };

  const parsed: Record<string, ScreeningRecord[]> = {};
  for (const [orgId, raw] of Object.entries(existing.data.data)) {
    try {
      const rows = JSON.parse(raw) as unknown;
      if (Array.isArray(rows) && rows.every(isScreeningRecord)) parsed[orgId] = rows;
      // A hand-edited or corrupt value is skipped, not fatal -- same
      // discipline lib/dpa-records.ts's getAll uses for its own
      // ConfigMap.
    } catch {
      // ignore -- malformed JSON for this org's key
    }
  }
  return { ok: true, data: parsed };
}

/**
 * Full screening register for one org, oldest-first, the exact shape GET
 * /api/owner/[orgId]/denied-party-screening returns. An org with no
 * screening history yet resolves to an empty array, not a 404 -- "never
 * screened" is a real, queryable, and itself review-worthy state, same
 * "no DPA recorded yet" discipline lib/dpa-records.ts's getDpaHistory
 * establishes.
 */
export async function getScreeningRegister(orgId: string): Promise<K8sResult<ScreeningRecord[]>> {
  const all = await getScreeningAll();
  if (!all.ok) return all;
  const records = (all.data[orgId] ?? []).slice().sort((a, b) => a.screenedAt.localeCompare(b.screenedAt));
  return { ok: true, data: records };
}

/**
 * Runs a real screening for one contact and appends the resulting
 * ScreeningRecord -- append-only, same read-modify-write-against-the-
 * live-ConfigMap-value discipline lib/dpa-records.ts's appendDpaRecord
 * uses. Never itself requires approval to RUN (screening is read-only
 * evidence-gathering, same "logging is not itself the sensitive action"
 * split lib/le-requests.ts's header comment documents for its own
 * ingest path) -- only a "potential_match" RESULT then requires a
 * maker-checker override before the org is considered cleared; see
 * `isOrgClearedForScreening`.
 */
export async function runAndRecordScreening(input: {
  orgId: string;
  contactRole: ContactRole;
  contactName: string;
  contactEmail: string;
  screenedByIdentifier: string;
}): Promise<K8sResult<ScreeningRecord>> {
  const list = await getListAll();
  if (!list.ok) return list;

  const matches = screenNameAgainstList(input.contactName, list.data);
  const record: ScreeningRecord = {
    id: globalThis.crypto.randomUUID(),
    orgId: input.orgId,
    contactRole: input.contactRole,
    contactName: input.contactName,
    contactEmail: input.contactEmail,
    result: matches.length > 0 ? "potential_match" : "clear",
    matches,
    screenedAt: new Date().toISOString(),
    screenedByIdentifier: input.screenedByIdentifier,
  };

  const all = await getScreeningAll();
  if (!all.ok) return all;
  const existingRecords = all.data[input.orgId] ?? [];
  const updatedRecords = [...existingRecords, record];

  const result = await createOrUpdateConfigMap(DENIED_PARTY_SCREENING_NAMESPACE, DENIED_PARTY_SCREENING_CONFIGMAP, {
    [input.orgId]: JSON.stringify(updatedRecords),
  });
  if (!result.ok) return result;
  return { ok: true, data: record };
}

export type RecordOverrideError = "not_found" | "already_decided" | "not_a_match" | "self_override";

/**
 * Records a real, second-approver override decision on a
 * "potential_match" screening record -- append-only via
 * read-modify-write, replacing only that one record's `override` field
 * (every other record in the org's array is round-tripped unchanged, the
 * same single-key-at-a-time merge lib/approval-workflow.ts's
 * recordApprovalDecision uses on its own ConfigMap). Refuses a decision
 * on a "clear" record (`not_a_match` -- there is nothing to override),
 * on a record that already has one (`already_decided` -- recorded
 * exactly once), and on a self-override (`decidedByIdentifier` equal to
 * the record's own `screenedByIdentifier`, same two-person-integrity
 * check lib/approval-workflow.ts's recordApprovalDecision enforces for
 * `requestedBy`/`approvedBy`). The caller (the route handler) is
 * expected to have ALREADY gated this behind
 * lib/approval-workflow.ts's `denied-party.override` maker-checker
 * approval -- this function performs the actual state write once that
 * approval exists, same "approval gate in the route, state write in the
 * lib" split every other maker-checker-guarded module in this repo
 * (lib/le-requests.ts's recordLeRequestResponse,
 * lib/subprocessors.ts's applySubprocessorChange) uses.
 */
export async function recordScreeningOverride(input: {
  orgId: string;
  screeningRecordId: string;
  decision: "cleared_to_proceed" | "confirmed_blocked";
  decidedByIdentifier: string;
  justification: string;
}): Promise<K8sResult<ScreeningRecord> | { ok: false; error: RecordOverrideError }> {
  const all = await getScreeningAll();
  if (!all.ok) return all;
  const orgRecords = all.data[input.orgId] ?? [];
  const index = orgRecords.findIndex((r) => r.id === input.screeningRecordId);
  if (index === -1) return { ok: false, error: "not_found" };

  const target = orgRecords[index];
  if (target.result !== "potential_match") return { ok: false, error: "not_a_match" };
  if (target.override) return { ok: false, error: "already_decided" };
  if (target.screenedByIdentifier === input.decidedByIdentifier) return { ok: false, error: "self_override" };

  const updatedRecord: ScreeningRecord = {
    ...target,
    override: {
      decision: input.decision,
      decidedByIdentifier: input.decidedByIdentifier,
      decidedAt: new Date().toISOString(),
      justification: input.justification,
    },
  };
  const updatedOrgRecords = [...orgRecords];
  updatedOrgRecords[index] = updatedRecord;

  const result = await createOrUpdateConfigMap(DENIED_PARTY_SCREENING_NAMESPACE, DENIED_PARTY_SCREENING_CONFIGMAP, {
    [input.orgId]: JSON.stringify(updatedOrgRecords),
  });
  if (!result.ok) return result;
  return { ok: true, data: updatedRecord };
}

/**
 * The real procurement-gate readout: `true` only if every screening
 * record on file for this org is either "clear" or a "potential_match"
 * that has been overridden with `"cleared_to_proceed"` -- an org with NO
 * screening history at all is NOT cleared (an unscreened org admin is
 * not evidence of anything), same fail-closed default
 * `isDpaSigned`-style checks in this repo use. A single
 * `"confirmed_blocked"` override, or a `"potential_match"` still
 * awaiting override, holds the whole org unresolved.
 */
export async function isOrgClearedForScreening(orgId: string): Promise<K8sResult<boolean>> {
  const register = await getScreeningRegister(orgId);
  if (!register.ok) return register;
  if (register.data.length === 0) return { ok: true, data: false };
  const cleared = register.data.every(
    (r) => r.result === "clear" || r.override?.decision === "cleared_to_proceed",
  );
  return { ok: true, data: cleared };
}
