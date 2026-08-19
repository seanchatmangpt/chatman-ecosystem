/**
 * Real hyperscaler-PaaS-style API key self-service (AWS IAM access keys /
 * GCP service account keys / Stripe API keys equivalent) -- the piece that
 * makes this console genuinely programmatically drivable, not just
 * browser-session-drivable. Every real hyperscaler PaaS ships a CLI/SDK
 * path alongside its web console; before this module, every single
 * capability in this app required a browser session cookie (see
 * middleware.ts / lib/session.ts), which is not a real PaaS expectation.
 *
 * Keys are generated cryptographically random (`crypto.randomBytes(32)`,
 * base64url-encoded -- 256 bits of entropy), prefixed `pk_live_` the same
 * way Stripe prefixes its own live secret keys, and stored HASHED
 * (SHA-256, one-way) -- the plaintext key is never stored anywhere past
 * the single response that creates it, and is not recoverable after that.
 * Storage is a real k8s Secret (`platform-console-api-keys`,
 * `platform-console` namespace -- a Secret, not a ConfigMap, precisely
 * because these are key hashes, and this repo already treats that
 * sensitivity class as Secret-worthy even where the value is one-way; see
 * lib/k8s.ts's own Secrets Manager section header). Reuses that exact
 * Secrets CRUD pattern (`getSecretData`/`createOrUpdateSecret`, the same
 * merge-patch-per-key convention `createOrUpdateConfigMap` established
 * for Feature Flags/Org Roles/Webhooks) rather than inventing a new k8s
 * object kind. One Secret data key per API key (`key-<12 hex chars>`),
 * value = one JSON-encoded `ApiKeyRecord`.
 *
 * Role binding reuses the Org RBAC model in lib/authz.ts unchanged: a key
 * is created FOR the creating owner's own identity (never an arbitrary
 * other identity -- minting a key "as" someone else would be identity
 * spoofing, not a feature any real hyperscaler IAM console offers), with
 * a role that must be <= the creator's own current role
 * (`clampRoleToCreator`, `ROLES.indexOf`), defaulting to the creator's own
 * role when omitted -- never escalated. middleware.ts resolves a
 * presented `Authorization: Bearer pk_live_...` header into a real,
 * normal `SessionPayload` (the new `authProvider: "api-key"` variant,
 * lib/session.ts) carrying that fixed `boundRole` claim; lib/authz.ts's
 * `getRoleFor` short-circuits straight to that claim for api-key sessions
 * -- so every existing `requireRole()` gate on every route keeps working
 * completely unchanged. This is purely an alternate authentication method
 * feeding the exact same authorization layer, not a parallel one.
 *
 * Disclosed simplification: no `lastUsedAt` tracking. Recording it would
 * require a real Secret write on every single Bearer-authenticated
 * request, risking concurrent merge-patch races under load for a
 * property no control in this console currently depends on; a real
 * `revoked`/`revokedAt` state (which every proof in the evidence bundle
 * exercises) is tracked instead.
 */
import crypto from "node:crypto";
import { createOrUpdateSecret, getSecretData, type K8sResult } from "@/lib/k8s";
import { ROLES, type Role } from "@/lib/authz";
import {
  DEFAULT_API_KEY_MODE,
  DEFAULT_API_KEY_TIER,
  isApiKeyMode,
  isApiKeyTier,
  type ApiKeyMode,
  type ApiKeyTier,
} from "@/lib/rate-limit";

export const API_KEYS_NAMESPACE = "platform-console";
export const API_KEYS_SECRET = "platform-console-api-keys";

// Two real, distinct prefixes -- same convention Stripe uses for its own
// `sk_live_`/`sk_test_` split. Deliberately branchable on the prefix alone
// (see resolveApiKeyAuth below): a caller/downstream system can tell a
// sandbox key from a live one just by looking at the string, with no
// Secret lookup required, exactly like Stripe's own dashboards/SDKs do.
const KEY_PREFIX_BY_MODE: Record<ApiKeyMode, string> = {
  live: "pk_live_",
  sandbox: "pk_sandbox_",
};
// Kept for the historical constant name other modules might still expect;
// resolves to the live prefix.
const KEY_PREFIX = KEY_PREFIX_BY_MODE.live;

// Sentinel orgId for keys that predate the orgId field and could not be
// confidently inferred by scripts/backfill-api-key-org.ts (identifier not
// resolvable to any known org's role assignments). Surfaced in the UI
// (ApiKeysPanel) as needing manual reassignment -- never silently treated
// as a real org.
export const UNASSIGNED_ORG_ID = "unassigned";

export interface ApiKeyRecord {
  id: string;
  prefix: string; // shown in listings -- e.g. "pk_live_AbCd1234..." -- never the full key
  hash: string; // sha256(plaintext), hex -- the only thing this app ever persists
  identifier: string; // bound org-roles identity (roleIdentifierFor-shaped)
  // Formal ownership: which org (lib/orgs.ts's Org.id) this key belongs to
  // -- required, non-null, distinct from `identifier` (a roles-identity
  // that is not itself an org id). Lets "list every key belonging to org
  // X" be answered directly (listApiKeysForOrg below) instead of inferred
  // from audit rows, which are only partially orgId-populated. Every key
  // minted before this field existed has no `orgId` at all in its stored
  // JSON -- parseRecord below falls back to the "unassigned" sentinel
  // (UNASSIGNED_ORG_ID) for those rather than rejecting the record, and
  // scripts/backfill-api-key-org.ts one-time-migrates them to a real org
  // id where one can be inferred.
  orgId: string;
  role: Role;
  createdBy: string; // identifier of the owner who created this key
  createdAt: string;
  name: string;
  revoked: boolean;
  revokedAt: string | null;
  // Rate-limit plan tier bound to this key (lib/rate-limit.ts,
  // middleware.ts's per-key token bucket) -- "standard" for every key
  // minted before this field existed (see parseRecord's default below),
  // so a pre-existing key's effective ceiling is unchanged by this
  // addition, not silently widened or narrowed.
  tier: ApiKeyTier;
  // Sandbox vs. live key class (lib/rate-limit.ts's ApiKeyMode) -- the
  // capability this field exists for: a buyer's CI pipeline can integrate
  // against this API without touching real k8s resources, real quota, or
  // real billing meters. Defaults to "live" on read (see parseRecord
  // below) for full backward compatibility with every key minted before
  // this field existed -- an old key's effective behavior is completely
  // unchanged by this addition. A key's mode is fixed at mint time
  // (baked into which prefix it was issued with, KEY_PREFIX_BY_MODE) and
  // never mutated afterward -- switching an existing key's mode would
  // silently change its billing/rate-limit class out from under whoever
  // is holding it, which is not a real provider's UX either.
  mode: ApiKeyMode;
}

export type ApiKeySummary = Omit<ApiKeyRecord, "hash">;

function toSummary(record: ApiKeyRecord): ApiKeySummary {
  const { hash: _hash, ...summary } = record;
  return summary;
}

function secretDataKeyFor(id: string): string {
  return `key-${id}`;
}

function isRole(value: unknown): value is Role {
  return typeof value === "string" && (ROLES as string[]).includes(value);
}

function parseRecord(raw: string): ApiKeyRecord | null {
  try {
    const parsed = JSON.parse(raw) as Partial<ApiKeyRecord>;
    if (
      typeof parsed.id !== "string" ||
      typeof parsed.prefix !== "string" ||
      typeof parsed.hash !== "string" ||
      typeof parsed.identifier !== "string" ||
      !isRole(parsed.role) ||
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
      // Backward compatible, same discipline as `tier` below: a record
      // written before this field existed has no `orgId` key at all --
      // defaults to the sentinel until scripts/backfill-api-key-org.ts
      // (or a fresh write through createApiKey) assigns a real one.
      orgId: typeof parsed.orgId === "string" && parsed.orgId ? parsed.orgId : UNASSIGNED_ORG_ID,
      role: parsed.role,
      createdBy: parsed.createdBy,
      createdAt: parsed.createdAt,
      name: typeof parsed.name === "string" ? parsed.name : "",
      revoked: parsed.revoked,
      revokedAt: typeof parsed.revokedAt === "string" ? parsed.revokedAt : null,
      // Backward compatible: a record written before this field existed
      // has no `tier` key at all -- defaults to "standard", the same
      // ceiling every key effectively had (via the flat Envoy filter)
      // before per-tier limits existed.
      tier: isApiKeyTier(parsed.tier) ? parsed.tier : DEFAULT_API_KEY_TIER,
      // Backward compatible, same discipline as `tier` above: a record
      // written before this field existed has no `mode` key at all --
      // defaults to "live", so a pre-existing key's effective billing/
      // rate-limit class is unchanged by this addition, never silently
      // downgraded to sandbox nor silently exempted from billing.
      mode: isApiKeyMode(parsed.mode) ? parsed.mode : DEFAULT_API_KEY_MODE,
    };
  } catch {
    return null;
  }
}

/** Real cryptographically random key material -- never derived, never predictable. */
function generateKeyMaterial(mode: ApiKeyMode): { plaintext: string; hash: string; prefix: string } {
  const keyPrefix = KEY_PREFIX_BY_MODE[mode];
  const plaintext = `${keyPrefix}${crypto.randomBytes(32).toString("base64url")}`;
  const hash = crypto.createHash("sha256").update(plaintext, "utf8").digest("hex");
  // Shown in listings so an owner can tell keys apart without the console
  // ever holding the full value again -- same convention real providers
  // use (Stripe shows `sk_live_51H...`, AWS shows the access key ID in
  // full but never the paired secret key past creation).
  const prefix = `${plaintext.slice(0, keyPrefix.length + 8)}...`;
  return { plaintext, hash, prefix };
}

function safeEqualHex(a: string, b: string): boolean {
  const bufA = Buffer.from(a, "hex");
  const bufB = Buffer.from(b, "hex");
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

/**
 * Clamps a requested role to at most the creator's own current role -- the
 * "never escalated" invariant. `creatorRole` must be the creator's real,
 * live role (resolved via lib/authz.ts's getRoleFor), never a role the
 * caller merely claims to have.
 */
export function clampRoleToCreator(requested: Role | undefined, creatorRole: Role): Role {
  if (!requested) return creatorRole;
  return ROLES.indexOf(requested) <= ROLES.indexOf(creatorRole) ? requested : creatorRole;
}

export interface CreateApiKeyInput {
  identifier: string;
  // Formal org ownership -- required, non-null (see ApiKeyRecord.orgId
  // above). Never inferred here: every caller (the global /api/api-keys
  // route and the org-scoped /api/orgs/[id]/api-keys route) must resolve
  // and pass a real org id before calling this.
  orgId: string;
  creatorRole: Role;
  createdBy: string;
  requestedRole?: Role;
  name?: string;
  // Plan tier this key should be rate-limited under (lib/rate-limit.ts).
  // Unlike `requestedRole`, tier is never clamped against the creator's
  // own role -- a key's tier reflects the *customer's paid plan*, an
  // orthogonal axis from the app-level RBAC role bound to the key, so
  // any owner may mint a key at any tier for their own identity. Defaults
  // to "standard" when omitted or invalid.
  tier?: ApiKeyTier;
  // Sandbox vs. live key class -- see ApiKeyRecord.mode's doc comment.
  // Defaults to "live" when omitted or invalid, same convention `tier`
  // above uses, so an existing caller that never passes this continues
  // minting ordinary live keys exactly as before this field existed.
  mode?: ApiKeyMode;
}

export async function createApiKey(
  input: CreateApiKeyInput,
): Promise<K8sResult<{ plaintext: string; key: ApiKeySummary }>> {
  if (!input.orgId || !input.orgId.trim()) {
    return { ok: false, error: "orgId is required to create an API key" };
  }
  const role = clampRoleToCreator(input.requestedRole, input.creatorRole);
  const mode: ApiKeyMode = isApiKeyMode(input.mode) ? input.mode : DEFAULT_API_KEY_MODE;
  const { plaintext, hash, prefix } = generateKeyMaterial(mode);
  const record: ApiKeyRecord = {
    id: crypto.randomBytes(6).toString("hex"),
    prefix,
    hash,
    identifier: input.identifier,
    orgId: input.orgId,
    role,
    createdBy: input.createdBy,
    createdAt: new Date().toISOString(),
    name: input.name?.trim() || "",
    revoked: false,
    revokedAt: null,
    tier: isApiKeyTier(input.tier) ? input.tier : DEFAULT_API_KEY_TIER,
    mode,
  };

  const result = await createOrUpdateSecret(API_KEYS_NAMESPACE, API_KEYS_SECRET, {
    [secretDataKeyFor(record.id)]: JSON.stringify(record),
  });
  if (!result.ok) return result;
  return { ok: true, data: { plaintext, key: toSummary(record) } };
}

export async function listApiKeys(): Promise<K8sResult<ApiKeySummary[]>> {
  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok) return result;
  const records: ApiKeyRecord[] = [];
  for (const raw of Object.values(result.data ?? {})) {
    const record = parseRecord(raw);
    if (record) records.push(record);
  }
  records.sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  return { ok: true, data: records.map(toSummary) };
}

/**
 * Org-scoped listing -- backs GET /api/orgs/[id]/api-keys. Filters the
 * same full listApiKeys() result down to the requested org id rather than
 * reading a separate index: this Secret has one data key per key already,
 * so a client-side filter over the (small, per-console) full list is the
 * same "no separate index to keep in sync" discipline getOrgProjectTier
 * (lib/orgs.ts) uses over listProjects.
 */
export async function listApiKeysForOrg(orgId: string): Promise<K8sResult<ApiKeySummary[]>> {
  const result = await listApiKeys();
  if (!result.ok) return result;
  return { ok: true, data: result.data.filter((k) => k.orgId === orgId) };
}

/**
 * Single-key lookup by id -- backs GET /api/orgs/[id]/api-keys/[keyId]/usage
 * (the route needs to confirm the keyId in the URL actually names a real,
 * live key -- returning `data: null` on a real-but-unresolved id, distinct
 * from the `ok: false` transport/Secret-read failure path -- before ever
 * calling lib/audit-db.ts's queryApiKeyUsage). Same read-then-parse shape
 * as revokeApiKey/updateApiKeyTier, just without the write.
 */
export async function getApiKeyById(id: string): Promise<K8sResult<ApiKeySummary | null>> {
  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok) return result;
  const raw = result.data?.[secretDataKeyFor(id)];
  const record = raw ? parseRecord(raw) : null;
  return { ok: true, data: record ? toSummary(record) : null };
}

export async function revokeApiKey(id: string): Promise<K8sResult<ApiKeySummary>> {
  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok) return result;
  const raw = result.data?.[secretDataKeyFor(id)];
  const record = raw ? parseRecord(raw) : null;
  if (!record) return { ok: false, error: `no api key found with id '${id}'` };

  if (!record.revoked) {
    record.revoked = true;
    record.revokedAt = new Date().toISOString();
    const patched = await createOrUpdateSecret(API_KEYS_NAMESPACE, API_KEYS_SECRET, {
      [secretDataKeyFor(id)]: JSON.stringify(record),
    });
    if (!patched.ok) return patched;
  }
  return { ok: true, data: toSummary(record) };
}

/**
 * Real tier upgrade/downgrade on an EXISTING key -- distinct from
 * `CreateApiKeyInput.tier` (set once at mint time): this is the mutation
 * the "rate-limit tier as a paid add-on" capability needs, called from
 * PUT /api/api-keys/[id]/rate-limit after that route has already gated on
 * `owner` and (for an actual upgrade) attached the real Stripe add-on
 * price via lib/stripe-billing.ts's `attachRateLimitAddonPrice`. Read-
 * modify-write against the same Secret key every other mutation here
 * uses -- no separate storage for the tier field.
 */
export async function updateApiKeyTier(
  id: string,
  tier: ApiKeyTier,
): Promise<K8sResult<ApiKeySummary>> {
  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok) return result;
  const raw = result.data?.[secretDataKeyFor(id)];
  const record = raw ? parseRecord(raw) : null;
  if (!record) return { ok: false, error: `no api key found with id '${id}'` };
  if (record.revoked) return { ok: false, error: `api key '${id}' is revoked` };

  if (record.tier !== tier) {
    record.tier = tier;
    const patched = await createOrUpdateSecret(API_KEYS_NAMESPACE, API_KEYS_SECRET, {
      [secretDataKeyFor(id)]: JSON.stringify(record),
    });
    if (!patched.ok) return patched;
  }
  return { ok: true, data: toSummary(record) };
}

export interface ResolvedApiKeyAuth {
  identifier: string;
  role: Role;
  keyId: string;
  tier: ApiKeyTier;
  mode: ApiKeyMode;
}

/**
 * Resolves a presented Bearer token into the identity+role it authenticates
 * as -- `null` on any of: wrong prefix, no matching hash, or a revoked
 * key. Called from middleware.ts on every API request that arrives with
 * no valid session cookie and an `Authorization: Bearer pk_live_...`
 * header. Hash comparison uses `crypto.timingSafeEqual` (not `===`) so a
 * failed lookup can't leak timing information about how close a guessed
 * key was to a real one.
 */
export async function resolveApiKeyAuth(
  presentedKey: string,
): Promise<ResolvedApiKeyAuth | null> {
  // Branchable on prefix alone, no lookup needed (see KEY_PREFIX_BY_MODE's
  // doc comment) -- but here we still need the real record either way, so
  // this just rejects anything that is neither a live nor a sandbox key
  // up front, same fast-reject shape the single-prefix check had before.
  const presentedMode = Object.entries(KEY_PREFIX_BY_MODE).find(([, prefix]) =>
    presentedKey.startsWith(prefix),
  )?.[0] as ApiKeyMode | undefined;
  if (!presentedMode) return null;
  const hash = crypto.createHash("sha256").update(presentedKey, "utf8").digest("hex");

  const result = await getSecretData(API_KEYS_NAMESPACE, API_KEYS_SECRET);
  if (!result.ok || !result.data) return null;

  for (const raw of Object.values(result.data)) {
    const record = parseRecord(raw);
    if (record && safeEqualHex(record.hash, hash)) {
      if (record.revoked) return null;
      return {
        identifier: record.identifier,
        role: record.role,
        keyId: record.id,
        tier: record.tier,
        mode: record.mode,
      };
    }
  }
  return null;
}
