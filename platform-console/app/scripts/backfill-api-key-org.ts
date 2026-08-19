/**
 * One-time backfill: assigns a real `orgId` (lib/api-keys.ts's
 * ApiKeyRecord.orgId) to every existing API key that predates the field.
 * Chicago style -- exercises the real k8s Secret/ConfigMap read/write
 * path (lib/k8s.ts's getSecretData/createOrUpdateSecret,
 * lib/authz.ts's getOrgRoleAssignmentsIn, lib/orgs.ts's listOrgs), no
 * mocked collaborators; asserts on real returned/persisted state.
 *
 * Inference: for each key missing `orgId`, walk every registered org
 * (lib/orgs.ts's listOrgs) and check whether the key's bound `identifier`
 * has a real role entry in that org's own `platform-console-org-roles`
 * ConfigMap (lib/authz.ts's getOrgRoleAssignmentsIn) -- the same
 * namespace-scoped role lookup requireRoleIn itself uses at request time.
 * A key whose identifier resolves to exactly one org gets that org's id.
 * A key whose identifier resolves to zero orgs (or, ambiguously, more
 * than one) falls back to the `UNASSIGNED_ORG_ID` sentinel
 * ("unassigned") -- never a guessed org id -- surfaced in ApiKeysPanel as
 * needing manual reassignment.
 *
 * Idempotent: a key that already carries a real (non-sentinel) `orgId`
 * is left untouched and not re-written.
 *
 * Run: npx tsx scripts/backfill-api-key-org.ts
 */
import {
  API_KEYS_NAMESPACE,
  API_KEYS_SECRET,
  UNASSIGNED_ORG_ID,
  type ApiKeyRecord,
} from "../lib/api-keys";
import { createOrUpdateSecret, getSecretData } from "../lib/k8s";
import { getOrgRoleAssignmentsIn } from "../lib/authz";
import { listOrgs } from "../lib/orgs";

function secretDataKeyFor(id: string): string {
  return `key-${id}`;
}

// Same lenient-parse-or-skip discipline as lib/api-keys.ts's parseRecord --
// a hand-edited/corrupt row is skipped, not fatal, and does not block the
// backfill of every other row.
function parseRawRecord(raw: string): ApiKeyRecord | null {
  try {
    const parsed = JSON.parse(raw) as Partial<ApiKeyRecord>;
    if (
      typeof parsed.id !== "string" ||
      typeof parsed.prefix !== "string" ||
      typeof parsed.hash !== "string" ||
      typeof parsed.identifier !== "string" ||
      typeof parsed.role !== "string" ||
      typeof parsed.createdBy !== "string" ||
      typeof parsed.createdAt !== "string" ||
      typeof parsed.revoked !== "boolean"
    ) {
      return null;
    }
    return {
      id: parsed.id,
      prefix: parsed.prefix,
      hash: parsed.hash,
      identifier: parsed.identifier,
      orgId: typeof parsed.orgId === "string" && parsed.orgId ? parsed.orgId : UNASSIGNED_ORG_ID,
      role: parsed.role as ApiKeyRecord["role"],
      createdBy: parsed.createdBy,
      createdAt: parsed.createdAt,
      name: typeof parsed.name === "string" ? parsed.name : "",
      revoked: parsed.revoked,
      revokedAt: typeof parsed.revokedAt === "string" ? parsed.revokedAt : null,
      tier: (parsed.tier as ApiKeyRecord["tier"]) ?? "standard",
    };
  } catch {
    return null;
  }
}

async function main() {
  const secretResult = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!secretResult.ok) {
    console.error(`FAIL: could not read ${API_KEYS_SECRET}: ${secretResult.error}`);
    process.exit(1);
  }
  const rawEntries = Object.entries(secretResult.data ?? {});
  if (rawEntries.length === 0) {
    console.log("no API keys found -- nothing to backfill");
    return;
  }

  const orgsResult = await listOrgs();
  if (!orgsResult.ok) {
    console.error(`FAIL: could not list orgs: ${orgsResult.error}`);
    process.exit(1);
  }
  const orgs = orgsResult.data;

  // Real role lookup per org, once each -- not once per key -- so an
  // install with many keys and few orgs does O(orgs) ConfigMap reads
  // total, not O(keys * orgs).
  const roleAssignmentsByOrgId = new Map<string, Set<string>>();
  for (const org of orgs) {
    const assignments = await getOrgRoleAssignmentsIn(org.namespace);
    if (!assignments.ok) {
      console.error(`FAIL: could not read role assignments for org '${org.id}': ${assignments.error}`);
      process.exit(1);
    }
    roleAssignmentsByOrgId.set(org.id, new Set(assignments.data.map((a) => a.identifier)));
  }

  let inferred = 0;
  let unassigned = 0;
  let skippedAlreadyAssigned = 0;
  let skippedCorrupt = 0;

  for (const [dataKey, raw] of rawEntries) {
    const record = parseRawRecord(raw);
    if (!record) {
      skippedCorrupt++;
      console.warn(`skip: '${dataKey}' is not a parseable ApiKeyRecord`);
      continue;
    }

    // Idempotent: only migrate keys that were actually written before
    // orgId existed (parseRawRecord's fallback set them to the sentinel
    // above -- a real stored orgId already present is left untouched).
    const rawParsedHasOrgId = (() => {
      try {
        const p = JSON.parse(raw) as Partial<ApiKeyRecord>;
        return typeof p.orgId === "string" && p.orgId.length > 0;
      } catch {
        return false;
      }
    })();
    if (rawParsedHasOrgId) {
      skippedAlreadyAssigned++;
      continue;
    }

    const matchingOrgIds = orgs
      .filter((org) => roleAssignmentsByOrgId.get(org.id)?.has(record.identifier))
      .map((org) => org.id);

    const resolvedOrgId = matchingOrgIds.length === 1 ? matchingOrgIds[0] : UNASSIGNED_ORG_ID;
    record.orgId = resolvedOrgId;

    const patched = await createOrUpdateSecret(API_KEYS_NAMESPACE, API_KEYS_SECRET, {
      [secretDataKeyFor(record.id)]: JSON.stringify(record),
    });
    if (!patched.ok) {
      console.error(`FAIL: could not write back key '${record.id}': ${patched.error}`);
      process.exit(1);
    }

    if (resolvedOrgId === UNASSIGNED_ORG_ID) {
      unassigned++;
      console.log(
        `key '${record.id}' (identifier '${record.identifier}') -> UNASSIGNED_ORG_ID ` +
          `(${matchingOrgIds.length === 0 ? "no matching org" : "ambiguous: multiple matching orgs"})`,
      );
    } else {
      inferred++;
      console.log(`key '${record.id}' (identifier '${record.identifier}') -> org '${resolvedOrgId}'`);
    }
  }

  console.log(
    `\ndone: ${inferred} inferred, ${unassigned} fell back to unassigned, ` +
      `${skippedAlreadyAssigned} already had a real orgId, ${skippedCorrupt} corrupt/skipped`,
  );
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
